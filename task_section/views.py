from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from auth_section.permissions import IsCustomAdminUser,IsSalesManagerUser
from .serializers import EventSerializer,Sales_Manager_EventSerializer,SalesManagerEventSerializer,FollowUpSerializer,AdminEventListSerializer,EventStatusSerializer,AdminEventStatusSerializer,AdminEventListWithStatusSerializer
from rest_framework.response import Response
from .models import Admin_event_list,Sales_Manager_Event,Sales_manager_Event_Status,Admin_Event_Status
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from datetime import timedelta, datetime 
from auth_section.models import Sales_manager_reg
from dateutil.parser import parse  # Better datetime parsing
from leads_section.models import Leads
from auth_section.models import Admin_reg
from followup_section.models import FollowUp
from django.http import JsonResponse
from django.utils.timezone import localtime, make_aware
from databank_section.models import DataBank
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now


# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def create_event(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    serializer = EventSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def update_event(request, id):
    admin = request.user

    # Check if the user has admin rights
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        event = Admin_event_list.objects.get(id=id)
    except Admin_event_list.DoesNotExist:
        return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check for datetime conflict only if date_time is being updated
    new_datetime_str = request.data.get("date_time")
    if new_datetime_str:
        try:
            new_datetime = datetime.fromisoformat(new_datetime_str)
            new_datetime = timezone.make_aware(new_datetime)

            # Check for booking conflict excluding current event
            if Admin_event_list.objects.exclude(id=id).filter(date_time=new_datetime).exists():
                return Response(
                    {"error": "This time slot is already booked. Choose another time."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Invalid datetime format. Use: YYYY-MM-DDTHH:MM:SS"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Perform update
    serializer = EventSerializer(event, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def delete_event(request, id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        event = Admin_event_list.objects.get(pk=id)
    except Admin_event_list.DoesNotExist:
        return Response({"error": "Event not found"}, status=status.HTTP_404_NOT_FOUND)

    # Convert event date_time to local time
    # event_time_local = timezone.localtime(event.date_time)
    # current_time_local = timezone.localtime(timezone.now())

    # # Prevent deletion if the event is within 24 hours
    # if event_time_local - current_time_local < timedelta(hours=0):
    #     return Response({"error": "You can only delete events at least 24 hours before the scheduled time."}, status=status.HTTP_400_BAD_REQUEST)

    event.delete()
    return Response({"message": "Event deleted successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])  # Allow only authenticated users
def list_upcomming_events(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    now = timezone.localdate()  # Get current local time
    events = Admin_event_list.objects.filter(date_time__gte=now).order_by('date_time')  # Filter and order by date_time
    serializer = AdminEventListWithStatusSerializer(events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])  # Allow only authenticated users
def sheduled_admin_events(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    events = Admin_event_list.objects.all()  # Filter and order by date_time
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)







@api_view(['POST'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def salesmanager_create_event(request):
    staff = request.user

    # Ensure staff exists
    sales_staff = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not sales_staff:
        return Response({'error': 'Invalid sales manager '}, status=status.HTTP_400_BAD_REQUEST)

    # Add staff ID to request data
    request_data = request.data.copy()
    request_data['staff'] = sales_staff.id  # Assign the staff ID

    # Serialize and validate data
    serializer = Sales_Manager_EventSerializer(data=request_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def Salesmanager_update_event(request, id):
    staff = request.user

    # Ensure staff exists
    sales_staff = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not sales_staff:
        return Response({'error': 'Invalid sales manager ID'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the event exists and belongs to the logged-in sales manager
    try:
        event = Sales_Manager_Event.objects.get(id=id, staff=sales_staff)
    except Sales_Manager_Event.DoesNotExist:
        return Response({"error": "Event not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

    # Convert event datetime to local timezone
    # event_time_local = timezone.localtime(event.date_time)
    # current_time_local = timezone.localtime(timezone.now())

    # # Prevent updates less than 24 hours before the event
    # if event_time_local - current_time_local < timedelta(hours=24):
    #     return Response(
    #         {"error": "Updates are only allowed at least 24 hours before the scheduled event."},
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    # Get new datetime from request
    new_datetime_str = request.data.get("date_time")

    if new_datetime_str:
        try:
            # Convert to datetime object in local timezone
            new_datetime = parse(new_datetime_str)
            if new_datetime.tzinfo is None:
                new_datetime = timezone.make_aware(new_datetime)  # Convert to aware datetime

            # Check if another event exists at this time (excluding the current event)
            if Sales_Manager_Event.objects.exclude(id=id).filter(date_time=new_datetime).exists():
                return Response(
                    {"error": "This time slot is already booked. Choose another time."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update the request data with the corrected datetime
            request.data["date_time"] = new_datetime.isoformat()

        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid datetime format. Use: YYYY-MM-DDTHH:MM:SS"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Update event with new data
    serializer = Sales_Manager_EventSerializer(event, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def salesmanager_delete_event(request, id):
    staff = request.user 

    # Ensure staff exists
    sales_staff = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not sales_staff:
        return Response({'error': 'Invalid sales manager ID'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the event exists and belongs to the logged-in sales manager
    try:
        event = Sales_Manager_Event.objects.get(id=id, staff=sales_staff)
    except Sales_Manager_Event.DoesNotExist:
        return Response({"error": "Event not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)

    # Convert event datetime to local timezone
    # event_time_local = timezone.localtime(event.date_time)
    # current_time_local = timezone.localtime(timezone.now())

    # # Prevent deletion if the event is within 24 hours
    # if event_time_local - current_time_local < timedelta(hours=0):
    #     return Response(
    #         {"error": "You can only delete events at least 24 hours before the scheduled time."},
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    event.delete()
    return Response({"message": "Event deleted successfully."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])  # Restrict access to sales managers only
def list_upcoming_salesmanager_events(request):
    staff_id = request.user

    # Ensure the sales manager exists
    sales_staff = Sales_manager_reg.objects.filter(user=staff_id.id).first()
    if not sales_staff:
        return Response({'error': 'Invalid sales manager ID'}, status=status.HTTP_400_BAD_REQUEST)

    now = timezone.now()  # Get current time

    # Filter events for the logged-in sales manager only
    events = Sales_Manager_Event.objects.filter(staff=sales_staff, date_time__gte=now).order_by('date_time')

    serializer = Sales_Manager_EventSerializer(events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)







@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def SalesManager_WorkHistory(request, salesmanager_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    # Get Sales Manager
    try:
        sales_manager = Sales_manager_reg.objects.get(id=salesmanager_id)
    except Sales_manager_reg.DoesNotExist:
        return Response({'error': 'Sales Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    # Fetch Leads followed by this Sales Manager
    leads = Leads.objects.filter(follower=sales_manager.username)

    # Count leads by their categories
    total_followed = leads.count()
    data_saved = leads.filter(stage="Data Saved").count()
    closed_successfully = leads.filter(stage="Closed Successfully").count()
    closed_by_someone = leads.filter(stage="Closed by Someone").count()
    dropped_leads = leads.filter(stage="Droped lead").count()
    pending_to_close = leads.exclude(
        stage__in=["Data Saved", "Closed Successfully", "Closed by Someone", "Droped lead"]
    ).count()

    # Calculate Lead Conversion Rate
    lead_conversion_rate = (closed_successfully / total_followed) * 100 if total_followed > 0 else 0

    # Response Data
    work_history = {
        "Sales Manager": {
            "id": sales_manager.id,
            "name": sales_manager.username,
            "email": sales_manager.email,
            "phone": sales_manager.phonenumber,
            "joined_date": sales_manager.joined_by,
        },
        "Work Summary": {
            "Total Leads Followed": total_followed,
            "Data Saved": data_saved,
            "Closed Successfully": closed_successfully,
            "Closed by Someone": closed_by_someone,
            "Dropped Leads": dropped_leads,
            "Pending to Close": pending_to_close,
            "Lead Conversion Rate (%)": round(lead_conversion_rate, 2),
        }
    }

    return Response(work_history, status=200)



@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def Personal_workhistory(request):
    sales_manager = request.user
    try:
        sales_manager = Sales_manager_reg.objects.get(user=sales_manager.id)
    except Sales_manager_reg.DoesNotExist:
        return Response({'error': 'Sales Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    # Fetch Leads followed by this Sales Manager
    leads = Leads.objects.filter(follower=sales_manager.user.username)

    # Count leads by their categories
    total_followed = leads.count()
    data_saved = leads.filter(stage="Data Saved").count()
    closed_successfully = leads.filter(stage="Closed Successfully").count()
    closed_by_someone = leads.filter(stage="Closed by Someone").count()
    dropped_leads = leads.filter(stage="Droped lead").count()
    pending_to_close = leads.exclude(
        stage__in=["Data Saved", "Closed Successfully", "Closed by Someone", "Droped lead"]
    ).count()

    # Calculate Lead Conversion Rate
    lead_conversion_rate = (closed_successfully / total_followed) * 100 if total_followed > 0 else 0

    # Response Data
    work_history = {
        "Sales Manager": {
            "id": sales_manager.id,
            "name": sales_manager.username,
            "email": sales_manager.email,
            "phone": sales_manager.phonenumber,
            "joined_date": sales_manager.joined_by,
        },
        "Work Summary": {
            "Total Leads Followed": total_followed,
            "Data Saved": data_saved,
            "Closed Successfully": closed_successfully,
            "Closed by Someone": closed_by_someone,
            "Dropped Leads": dropped_leads,
            "Pending to Close": pending_to_close,
            "Lead Conversion Rate (%)": round(lead_conversion_rate, 2),
        }
    }

    return Response(work_history, status=200)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def CRM_performance_graph(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    # Fetch all leads
    total_leads = Leads.objects.count()
    data_saved = DataBank.objects.count()
    new_leads = Leads.objects.filter(staff_id=0).count()
    closed_successfully = Leads.objects.filter(stage="Closed Successfully").count()
    closed_by_someone = Leads.objects.filter(stage="Closed by Someone").count()
    dropped_leads = Leads.objects.filter(stage="Droped lead").count()
    pending_to_close = Leads.objects.exclude(
        stage__in=["Data Saved", "Closed Successfully", "Closed by Someone", "Droped lead"]
    ).count()

    # Calculate Lead Conversion Rate
    lead_conversion_rate = (closed_successfully / total_leads) * 100 if total_leads > 0 else 0

    # Response Data
    crm_summary = {
        "CRM Performance Summary": {
            "Total Leads": total_leads,
            "New Leads":new_leads,
            "Data Saved": data_saved,
            "Closed Successfully": closed_successfully,
            "Unsuccessfully Closed leads": closed_by_someone + dropped_leads,
            "Lead Conversion Rate (%)": round(lead_conversion_rate, 2),
        }
    }

    return Response(crm_summary, status=200)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def get_scheduled_works(request):
    staff = request.user
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user = staff.id).first()
    selected_date = request.query_params.get("date")  # Expected format: YYYY-MM-DD
    
    if not selected_date:
        return Response({"error": "Date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    start_datetime = make_aware(datetime.combine(selected_date, datetime.min.time()))
    end_datetime = make_aware(datetime.combine(selected_date, datetime.max.time()))

    events = Sales_Manager_Event.objects.filter(date_time__range=(start_datetime, end_datetime),staff=salesmanager)
    followups = FollowUp.objects.filter(followup_date__range=(start_datetime, end_datetime),follower=salesmanager)

    events_data = SalesManagerEventSerializer(events, many=True).data
    followups_data = FollowUpSerializer(followups, many=True).data

    return Response({"events": events_data, "followups": followups_data}, status=status.HTTP_200_OK)




@api_view(["GET"])
@permission_classes([IsAuthenticated,IsCustomAdminUser])  # Restrict access to admin users
def get_admin_scheduled_works(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    
    selected_date = request.query_params.get("date")

    if not selected_date:
        return Response({"error": "Date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    start_datetime = make_aware(datetime.combine(selected_date, datetime.min.time()))
    end_datetime = make_aware(datetime.combine(selected_date, datetime.max.time()))

    # Get events for the selected date
    events = Admin_event_list.objects.filter(date_time__range=(start_datetime, end_datetime))

    events_data = AdminEventListSerializer(events, many=True).data

    return Response({"admin_events": events_data}, status=status.HTTP_200_OK)








@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def Admin_Salesmanager_workhistory(request,staff_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    sales_manager = Sales_manager_reg.objects.filter(id=staff_id).first()

    # Fetch Leads followed by this Sales Manager
    leads = Leads.objects.filter(follower=sales_manager.user.username)

    # Count leads by their categories
    total_followed = leads.count()
    data_saved = leads.filter(stage="Data Saved").count()
    closed_successfully = leads.filter(stage="Closed Successfully").count()
    closed_by_someone = leads.filter(stage="Closed by Someone").count()
    dropped_leads = leads.filter(stage="Droped lead").count()
    pending_to_close = leads.exclude(
        stage__in=["Data Saved", "Closed Successfully", "Closed by Someone", "Droped lead"]
    ).count()

    # Calculate Lead Conversion Rate
    lead_conversion_rate = (closed_successfully / total_followed) * 100 if total_followed > 0 else 0

    # Response Data
    work_history = {
        "Sales Manager": {
            "id": sales_manager.id,
            "photo": sales_manager.photo.url if sales_manager.photo else None,
            "name": sales_manager.username,
            "email": sales_manager.email,
            "phone": sales_manager.phonenumber,
            "joined_date": sales_manager.joined_by,
        },
        "Work Summary": {
            "Total Leads Followed": total_followed,
            "Data Saved": data_saved,
            "Closed Successfully": closed_successfully,
            "Closed by Someone": closed_by_someone,
            "Dropped Leads": dropped_leads,
            "Pending to Close": pending_to_close,
            "Lead Conversion Rate (%)": round(lead_conversion_rate, 2),
        }
    }

    return Response(work_history, status=200)





from datetime import datetime, time


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def Todays_upcomming_events(request):
    admin = request.user

    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    today = timezone.localdate()  # e.g., 2025-04-09
    start_of_day = make_aware(datetime.combine(today, time.min))  # 00:00
    end_of_day = make_aware(datetime.combine(today, time.max))    # 23:59:59.999999

    events = Admin_event_list.objects.filter(date_time__range=(start_of_day, end_of_day)).order_by('date_time')

    serializer = EventSerializer(events, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)








@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def get_event_reminder_admin(request):
    admin = request.user

    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    current_time = now()
    local_current_time = localtime(current_time)
    reminder_time = local_current_time + timedelta(minutes=5)  # Follow-ups happening in 5 minutes

   

   
    upcoming_events = Admin_event_list.objects.filter(
        date_time__gte = local_current_time,
        date_time__lte = reminder_time
    ).values("id","date_time","event_name","priority","notes")

    
    event_notifications = [
        {
            "type": "event",
            "message": f"📅 Event Alert: '{e['event_name']}' is scheduled in 5 minutes at {localtime(e['date_time']).strftime('%Y-%m-%d %H:%M')}. Priority: {e['priority']}. Notes: {e['notes']}"

        }
        for e in upcoming_events
    ]
    notifications = event_notifications

    return Response({
        "notifications": notifications,
        "time": local_current_time
    })
    
    
    
    



@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def SM_Event_status_entry(request, event_id):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    try:
        event = Sales_Manager_Event.objects.get(id=event_id,staff = salesmanager)
    except Sales_Manager_Event.DoesNotExist:
        return Response({"error": "Follow-up not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the followup already has a status
    try:
        existing_status = Sales_manager_Event_Status.objects.get(event=event)
    except Sales_manager_Event_Status.DoesNotExist:
        existing_status = None

    serializer = EventStatusSerializer(instance=existing_status, data=request.data)

    if serializer.is_valid():
        serializer.save(event=event)
        return Response(serializer.data, status=status.HTTP_200_OK if existing_status else status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    
    
    
    
    
    
    
    
@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def Admin_Event_status_entry(request, event_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        event = Admin_event_list.objects.get(id=event_id)
    except Admin_event_list.DoesNotExist:
        return Response({"error": "Follow-up not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the followup already has a status
    try:
        existing_status = Admin_Event_Status.objects.get(admin_event=event)
    except Admin_Event_Status.DoesNotExist:
        existing_status = None

    serializer = AdminEventStatusSerializer(instance=existing_status, data=request.data)

    if serializer.is_valid():
        serializer.save(admin_event=event)
        return Response(serializer.data, status=status.HTTP_200_OK if existing_status else status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)