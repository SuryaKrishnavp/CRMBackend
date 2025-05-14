from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Leads,LeadCategory
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.decorators import api_view,permission_classes
from .serializers import LeadsViewSerializer,EnterLeadsSerializer,AdminEnterLeadsSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from auth_section.permissions import IsSalesManagerUser,IsCustomAdminUser
from auth_section.models import Sales_manager_reg
from databank_section.models import DataBank
from datetime import timedelta
from django.utils.timezone import now
from .tasks import send_followup_email
from celery import current_app
from rest_framework import status
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils.timezone import localtime

# Create your views here.
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def receive_form_submission(request):
    if request.method == "POST":
        try:
            raw_data = request.body.decode('utf-8')
            
            # Try to parse incoming JSON
            data = json.loads(raw_data)

            # Validate required fields
            required_fields = ["name", "email", "phonenumber", "district", "place", "address", "purpose", "mode_of_purpose"]
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({"error": f"Missing required field: {field}"}, status=400)


            lead = Leads.objects.create(
                timestamp=timezone.now(),  # Use server timestamp
                name=data.get("name", "").strip(),
                email=data.get("email", "").strip(),
                phonenumber=data.get("phonenumber", "").strip(),
                district=data.get("district", "").strip(),
                place=data.get("place", "").strip(),
                address=data.get("address","").strip(),
                purpose=data.get("purpose", "").strip(),
                mode_of_purpose=data.get("mode_of_purpose","").strip(),
                message=data.get("message", "").strip(),
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "notifications_group",
                {
                    "type": "send_notification",
                    "message": f"New lead received! Name: {lead.name}, District: {lead.district}, Purpose: {lead.purpose}",
                },
            )

            return JsonResponse({"message": "Lead saved successfully!"}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)




@api_view(['GET'])
@permission_classes([AllowAny])
def view_leads(request):
    if request.method == "GET":
        data = Leads.objects.all()
        serializer = LeadsViewSerializer(data,many=True)
        return Response(serializer.data)
    else:
        return Response({'message':"Something went wrong"})
    

@api_view(['POST'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def Follow_lead(request,lead_id):
    SManager = request.user
    sales_manager = Sales_manager_reg.objects.filter(user=SManager.id).first()
    lead = Leads.objects.filter(id=lead_id).first()  
    
    if not lead:
        return Response({"error": "Lead not found"}, status=404)

    if lead.staff_id != 0:
        return Response({"error": "This lead is already being followed by another sales manager"}, status=400)
    lead.follower = sales_manager.user.username
    lead.staff_id = sales_manager.id
    lead.status = "Followed"
    lead.save()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "lead_notifications",
        {
            "type": "send_notification",
            "message": {
                "follower":lead.follower,
                "lead_id": lead.id,
                "message": f"{lead.follower}  followed the Lead({lead.id}) successfully"
            }
        }  
    )
    return Response({'message': "Successfully followed the lead"}, status=200)


@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def Update_lead_stage(request,lead_id):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    sales_manager = Sales_manager_reg.objects.filter(user=staff.id).first()
    salesmanger_id = sales_manager.id
    lead = Leads.objects.filter(id=lead_id,staff_id=salesmanger_id).first()  
    
    if not lead:
        return Response({"error": "Lead not found"}, status=404)

    updated_stage = request.data.get("stage")
    if updated_stage in ["Closed Successfully", "Closed by Someone", "Droped Lead"]:
        saved_data = DataBank.objects.filter(lead=lead).first()
        if saved_data:
            saved_data.delete()
        if not lead.closed_date:
            lead.closed_date = now().date()

        if updated_stage in ["Closed by Someone", "Droped Lead"]:
            send_followup_email.apply_async((lead.id,), eta=now() + timedelta(days=365))
    lead.stage = updated_stage
    lead.save()  
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "lead_notifications",
        {
            "type": "send_notification",
            "message": {
                "follower":lead.follower,
                "lead_id": lead.id,
                "new_stage": updated_stage,
                "message": "Lead stage updated successfully"
            }
        }
    )
    
    return Response({'message': "Successfully updated stage"}, status=200)





@api_view(['POST'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def manually_enter_leads(request):
    staff = request.user
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({'message':'Unauthorized user'})
    serializer = EnterLeadsSerializer(data=request.data)
    if serializer.is_valid():
        lead = serializer.save()  
        lead.follower = salesmanager.user.username  
        lead.staff_id = salesmanager.id 
        lead.status = "Followed" 
        lead.save()  

        return Response({'message': 'Lead added successfully'}, status=201)
    
    return Response(serializer.errors, status=400)
        

@api_view(['PATCH'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def add_follower(request,lead_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    lead = Leads.objects.filter(id=lead_id).first()  
    
    if not lead:
        return Response({"error": "Lead not found"}, status=404)
    sales_manager_id = request.data.get('sales_manager_id')
    if not sales_manager_id:
        return Response({"error": "Sales Manager ID is required"}, status=400)

    sales_manager = Sales_manager_reg.objects.filter(id=sales_manager_id).first()
    if not sales_manager:
        return Response({"error": "Sales Manager not found"}, status=404)
    lead.follower = sales_manager.user.username
    lead.staff_id = sales_manager.id
    lead.status = "Followed"
    lead.save()
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "lead_notifications",
        {
            "type": "send_notification",
            "message": {
                "follower":lead.follower,
                "lead_id": lead.id,
                "message": f"{lead.follower} followed Lead id:({lead.id}) successfully"
            }
        }  
    )
    send_follower_email(sales_manager, lead)
    return Response({'message': "Successfully add follower to the lead"}, status=200)

def send_follower_email(sales_manager, lead):
    subject = f"New Lead Assigned: {lead.id}"
    message = f"""
    Dear {sales_manager.username},

    You have been added as a follower to Lead ID: {lead.id}.
    
    Lead Details:
    - Lead Name: {lead.name}
    - Lead Status: {lead.status}

    Please log in to your account to manage and follow up with the lead.

    Regards,
    DEVLOK CRM Team
    """
    
    from_email = 'jrdjangodeveloper@gmail.com'
    recipient_list = [sales_manager.email]  # Send to sales manager's email
    
    # Send email
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    
    
from datetime import datetime


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def get_lead_closure_stats(request, salesmanager_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    today = now().date()
    start_of_month = today.replace(day=1)  # First day of current month
    start_of_month_datetime = datetime.combine(start_of_month, datetime.min.time())

    # ✅ Get total leads for this Sales Manager created this month
    total_leads = Leads.objects.filter(
        staff_id=salesmanager_id,
        timestamp__gte=start_of_month_datetime
    ).count()

    # ✅ Get successfully closed leads in this month
    closed_successfully = Leads.objects.filter(
        staff_id=salesmanager_id,
        stage="Closed Successfully",
        closed_date__isnull=False,  # Only leads that have a closed date
        closed_date__gte=start_of_month
    ).count()

    # ✅ Calculate percentage of leads closed successfully
    success_percentage = (
        (closed_successfully / total_leads) * 100 if total_leads > 0 else 0
    )

    # ✅ Response for graph plotting
    response_data = {
        "total_leads": total_leads,
        "closed_successfully": closed_successfully,
        "success_percentage": round(success_percentage, 2),
    }

    return Response(response_data, status=200)







@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])  # Ensure the user is authenticated and a Sales Manager
def salesmanager_monthly_performance(request):
    # The user is automatically set via JWT
    salesmanager = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(salesmanager, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)

    staff = Sales_manager_reg.objects.filter(user=salesmanager.id).first()
    
    # Calculate the start of the current month
    today = now().date()
    start_of_month = today.replace(day=1)  # First day of current month
    start_of_month_datetime = datetime.combine(start_of_month, datetime.min.time())

    # Get total leads for this Sales Manager created this month
    total_leads = Leads.objects.filter(
        staff_id=staff.id,
        timestamp__gte=start_of_month_datetime
    ).count()

    # Get successfully closed leads in this month
    closed_successfully = Leads.objects.filter(
        staff_id=staff.id,
        stage="Closed Successfully",
        closed_date__isnull=False,  # Only leads that have a closed date
        closed_date__gte=start_of_month
    ).count()

    # Calculate percentage of leads closed successfully
    success_percentage = (
        (closed_successfully / total_leads) * 100 if total_leads > 0 else 0
    )

    # Prepare the response data for graph plotting
    response_data = {
        "total_leads": total_leads,
        "closed_successfully": closed_successfully,
        "success_percentage": round(success_percentage, 2),
    }

    return Response(response_data, status=200)






@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def leads_graph_data(request):
    admin = request.user
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    purposes = [
        'For Buying a Property',
        'For Selling a Property',
        'For Rental or Lease',
        'Looking to Rent or Lease Property'
    ]

    # Filter only for relevant purposes to reduce DB scan
    queryset = Leads.objects.filter(purpose__in=purposes)

    # Aggregate all required counts grouped by purpose
    aggregated = (
        queryset
        .values('purpose')
        .annotate(
            total_leads=Count('id'),
            data_saved_leads=Count('id', filter=Q(stage="Data Saved")),
            closed_successfully_leads=Count('id', filter=Q(stage="Closed Successfully")),
            unsuccessfully_closed_leads=Count('id', filter=Q(stage__in=["Closed by Someone", "Dropped Lead"])),
            new_leads=Count('id', filter=Q(stage="Not Opened"))
        )
    )

    # Ensure all purposes are present even if 0
    data_by_purpose = {entry['purpose']: entry for entry in aggregated}
    graph_data = []

    for purpose in purposes:
        graph_data.append({
            "purpose": purpose,
            "total_leads": data_by_purpose.get(purpose, {}).get('total_leads', 0),
            "data_saved_leads": data_by_purpose.get(purpose, {}).get('data_saved_leads', 0),
            "closed_successfully_leads": data_by_purpose.get(purpose, {}).get('closed_successfully_leads', 0),
            "unsuccessfully_closed_leads": data_by_purpose.get(purpose, {}).get('unsuccessfully_closed_leads', 0),
            "new_leads": data_by_purpose.get(purpose, {}).get('new_leads', 0),
        })

    return Response({"graph_data": graph_data}, status=200)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_new_leads(request):
    
    leads = Leads.objects.filter(stage="Not Opened",status="Pending").order_by('-timestamp')
    
    # Serialize leads data
    serializer = LeadsViewSerializer(leads, many=True)
    
    return Response(serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def get_DataSaved_leads(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    # Get leads with status = "Not Opened" and order by timestamp (newest first)
    leads = Leads.objects.filter(stage="Data Saved").order_by('-timestamp')
    
    # Serialize leads data
    serializer = LeadsViewSerializer(leads, many=True)
    
    return Response(serializer.data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def get_successfullyclosed_leads(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    # Get leads with status = "Not Opened" and order by timestamp (newest first)
    leads = Leads.objects.filter(stage="Closed Successfully").order_by('-timestamp')
    
    # Serialize leads data
    serializer = LeadsViewSerializer(leads, many=True)
    
    return Response(serializer.data, status=200)


from django.db.models import Q

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def get_unsuccessfullyclosed_leads(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    # Get leads with status = "Not Opened" and order by timestamp (newest first)
    leads = Leads.objects.filter(
        Q(stage="Closed by Someone") | Q(stage="Dropped Lead")
    ).order_by('-timestamp')    
    # Serialize leads data
    serializer = LeadsViewSerializer(leads, many=True)
    
    return Response(serializer.data, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def get_pending_leads(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    # Get leads with status = "Not Opened" and order by timestamp (newest first)
    leads = Leads.objects.filter(
        Q(stage="Not Opened") | Q(stage="Data Saved")
    ).order_by('-timestamp')    
    # Serialize leads data
    serializer = LeadsViewSerializer(leads, many=True)
    
    return Response(serializer.data, status=200)








from django.db.models import Count, Q

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def salesmanger_leads_graph(request):
    staff = request.user

    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = staff.sales_manager_reg  # Use reverse relation directly

    purposes = [
        'For Buying a Property',
        'For Selling a Property',
        'For Rental or Lease',
        'Looking to Rent or Lease Property'
    ]

    # Fetch all relevant leads in one query
    leads = Leads.objects.filter(staff_id=salesmanager.id)

    # Annotate the counts grouped by purpose and stage
    grouped = leads.values('purpose', 'stage').annotate(count=Count('id'))

    # Also get count of new leads separately (not filtered by staff)
    new_leads_raw = Leads.objects.filter(stage="Not Opened").values('purpose').annotate(count=Count('id'))
    new_leads_map = {item['purpose']: item['count'] for item in new_leads_raw}

    # Organize data into a summary dictionary
    summary = {purpose: {
        "purpose": purpose,
        "total_leads": 0,
        "data_saved_leads": 0,
        "closed_successfully_leads": 0,
        "unsuccessfully_closed_leads": 0,
        "new_leads": new_leads_map.get(purpose, 0),
    } for purpose in purposes}

    for item in grouped:
        purpose = item['purpose']
        stage = item['stage']
        count = item['count']
        if purpose not in summary:
            continue

        summary[purpose]["total_leads"] += count

        if stage == "Data Saved":
            summary[purpose]["data_saved_leads"] = count
        elif stage == "Closed Successfully":
            summary[purpose]["closed_successfully_leads"] = count
        elif stage in ["Closed by Someone", "Dropped Lead"]:
            summary[purpose]["unsuccessfully_closed_leads"] += count

    return Response({"graph_data": list(summary.values())}, status=200)






@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def get_followedleads_salesmanager(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    salesmanager = Sales_manager_reg.objects.filter(user = staff.id).first()
    new_leads = Leads.objects.filter(staff_id=salesmanager.id,status="Followed").order_by('-timestamp')
    serializer = LeadsViewSerializer(new_leads,many=True).data
    return Response(serializer,status=200)





@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def followed_leads_salesmanager(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first() 
    
    followed_leads = Leads.objects.filter(staff_id=salesmanager.id,stage="Not opened").order_by('-timestamp')
    serializer = LeadsViewSerializer(followed_leads,many=True).data
    return Response(serializer,status=200)



@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def datasaved_leads_salesmanager(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    datasaved_leads = Leads.objects.filter(staff_id=salesmanager.id,stage="Data Saved").order_by('-timestamp')
    serializer = LeadsViewSerializer(datasaved_leads,many=True).data
    return Response(serializer,status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def successfully_closed_leads_salesmanager(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    successfully_closed_leads = Leads.objects.filter(staff_id=salesmanager.id,stage="Closed Successfully").order_by('-timestamp')
    serializer = LeadsViewSerializer(successfully_closed_leads,many=True).data
    return Response(serializer,status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def unsuccessfully_closed_leads_salesmanager(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    
    leads = Leads.objects.filter(
        staff_id=salesmanager.id,  # ✅ Filter by staff_id only
        stage__in=["Closed by Someone", "Droped Lead"]  # ✅ Stage condition
    ).order_by('-timestamp')
    serializer = LeadsViewSerializer(leads,many=True).data
    return Response(serializer,status=200)



@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def pending_leads_salesmanager(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    
    leads = Leads.objects.filter(
        staff_id=salesmanager.id,  
        stage__in=["Not Opened", "Data Saved"]  
    ).order_by('-timestamp')
    serializer = LeadsViewSerializer(leads,many=True).data
    return Response(serializer,status=200)





@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def get_unrecorded_salesmanager(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    salesmanager = Sales_manager_reg.objects.filter(user = staff.id).first()
    new_leads = Leads.objects.filter(staff_id=salesmanager.id,status="Followed",stage="Not Opened").order_by('-timestamp')
    serializer = LeadsViewSerializer(new_leads,many=True).data
    return Response(serializer,status=200)





from collections import defaultdict  # <- THIS was missing



@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def salesmanager_crm_performance_graph(request):
    staff = request.user

    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)

    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not salesmanager:
        return Response({"error": "Sales Manager not found"}, status=status.HTTP_404_NOT_FOUND)

    leads = Leads.objects.filter(staff_id=salesmanager.id)

    monthly_data = defaultdict(lambda: {"total": 0, "closed": 0})

    for lead in leads:
        if not lead.timestamp:
            continue

        month_key = lead.timestamp.strftime('%Y-%m')
        monthly_data[month_key]["total"] += 1

        if lead.stage == 'Closed Successfully' and lead.closed_date:
            monthly_data[month_key]["closed"] += 1

    result = []
    for month, data in sorted(monthly_data.items()):
        total = data["total"]
        closed = data["closed"]
        conversion_rate = round((closed / total) * 100, 2) if total else 0.0

        result.append({
            "month": month,
            "total_leads": total,
            "closed_success": closed,
            "conversion_rate": conversion_rate
        })

    return Response(result, status=status.HTTP_200_OK)







@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def salesmanager_crm_graph_Leads(request):
    staff = request.user

    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=status.HTTP_403_FORBIDDEN)

    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    total_leads = Leads.objects.filter(staff_id=salesmanager.id).count()
    successfully_closed = Leads.objects.filter(staff_id=salesmanager.id,stage="Closed Successfully").count()
    unsuccess_leads = Leads.objects.filter(staff_id=salesmanager.id,
                                           stage__in=["Closed by Someone", "Dropped Lead"]).count()
    unrecorded_leads=Leads.objects.filter(staff_id=salesmanager.id,stage="Not Opened").count()
    
    return Response({
        "total_leads": total_leads,
        "successfully_closed": successfully_closed,
        "unsuccess_leads": unsuccess_leads,
        "unrecorded_leads": unrecorded_leads
    }, status=status.HTTP_200_OK)
    
    
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def Admin_crm_performance_graph(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    

    leads = Leads.objects.all()

    monthly_data = defaultdict(lambda: {"total": 0, "closed": 0})

    for lead in leads:
        if not lead.timestamp:
            continue

        month_key = lead.timestamp.strftime('%Y-%m')
        monthly_data[month_key]["total"] += 1

        if lead.stage == 'Closed Successfully' and lead.closed_date:
            monthly_data[month_key]["closed"] += 1

    result = []
    for month, data in sorted(monthly_data.items()):
        total = data["total"]
        closed = data["closed"]
        conversion_rate = round((closed / total) * 100, 2) if total else 0.0

        result.append({
            "month": month,
            "total_leads": total,
            "closed_success": closed,
            "conversion_rate": conversion_rate
        })

    return Response(result, status=status.HTTP_200_OK)







@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def Admin_crm_graph_Leads(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    total_leads = Leads.objects.all().count()
    successfully_closed = Leads.objects.filter(stage="Closed Successfully").count()
    unsuccess_leads = Leads.objects.filter(stage__in=["Closed by Someone", "Dropped Lead"]).count()
    unrecorded_leads=Leads.objects.filter(stage="Not Opened").count()
    
    return Response({
        "total_leads": total_leads,
        "successfully_closed": successfully_closed,
        "unsuccess_leads": unsuccess_leads,
        "unrecorded_leads": unrecorded_leads
    }, status=status.HTTP_200_OK)
    
    
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def followed_leads_admin(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    followed_leads = Leads.objects.filter(status="Followed").order_by('-timestamp')
    serializer = LeadsViewSerializer(followed_leads,many=True).data
    return Response(serializer,status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def unrecorded_leads_admin(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    followed_leads = Leads.objects.filter(status="Followed",stage="Not Opened").order_by('-timestamp')
    serializer = LeadsViewSerializer(followed_leads,many=True).data
    return Response(serializer,status=200)






@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def admin_manually_enter_leads(request):
    admin_user = request.user

    # Check if the user has the admin profile
    if not hasattr(admin_user, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    serializer = AdminEnterLeadsSerializer(data=request.data)

    if serializer.is_valid():
        lead = serializer.save()  # Saved lead instance
        follower_name = lead.follower
        try:
            follower_user = Sales_manager_reg.objects.get(username=follower_name, is_sales_manager=True)
        except Sales_manager_reg.DoesNotExist:
            return Response({'error': 'Follower not found or not a sales manager'}, status=404)

        # ✅ Send email notification
        send_follower_email(follower_user, lead)

        # ✅ Send real-time notification
        channel_layer = get_channel_layer()
        notification = {
            'type': 'lead_notification',
            'message': f"Follower: {follower_user.username} assigned a new lead. Check your Followed Leads section."
        }
        async_to_sync(channel_layer.group_send)(f"user_{follower_user.id}", notification)

        return Response({'message': 'Lead added successfully'}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def Delete_lead(request,lead_id):
    admin_user = request.user

    # Check if the user has the admin profile
    if not hasattr(admin_user, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    lead = Leads.objects.filter(id=lead_id).first()
    lead.delete()
    return Response({'message':"lead deleted successfully"})








@api_view(['GET'])  # Changed to GET since we're retrieving data
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def lead_category_graph(request):
    admin_user = request.user

    # Check if the user has the admin profile
    if not hasattr(admin_user, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    # Count how many leads belong to each category
    category_counts = (
        LeadCategory.objects
        .values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return Response(category_counts)







@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def lead_category_current_month(request):
    admin_user = request.user

    if not hasattr(admin_user, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    today = now().date()
    first_day_of_month = today.replace(day=1)

    monthly_data = (
        LeadCategory.objects
        .filter(timestamp__date__gte=first_day_of_month)
        .values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    return Response({
        'month': first_day_of_month.strftime('%Y-%m'),
        'data': monthly_data
    })