from django.shortcuts import render
from .models import FollowUp,Followup_status
from rest_framework.decorators import api_view,permission_classes
from auth_section.permissions import IsSalesManagerUser
from .serializers import FollowUpSerializer,FollowUpWithCustomerSerializer,FollowupStatusSerializer
from leads_section.models import Leads
from rest_framework.response import Response
from auth_section.models import Sales_manager_reg
from django.http import JsonResponse
import datetime
from django.utils import timezone
from rest_framework import status
from django.utils.timezone import now,localtime
from datetime import timedelta
from task_section.models import Sales_Manager_Event
from task_section.serializers import Sales_Manager_EventSerializer,SalesManagerEventSerializer
from rest_framework.permissions import IsAuthenticated
import logging
from django.db import transaction
# from followup_section.tasks import send_followup_notification_task
import logging
from .tasks import send_followup_notifications 
# Create your views here.



logger = logging.getLogger(__name__)

from django.db import transaction

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def create_followup(request, lead_id):
    staff = request.user

    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)

    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()

    try:
        lead = Leads.objects.get(id=lead_id)
    except Leads.DoesNotExist:
        return Response({"error": "Lead not found"}, status=404)

    serializer = FollowUpSerializer(data=request.data)
    if serializer.is_valid():
        followup_date = serializer.validated_data.get("followup_date")
        followup_date = localtime(followup_date)
        existing_followup = FollowUp.objects.filter(
            follower=salesmanager,
            followup_date=followup_date
        ).exists()

        if existing_followup:
            return Response({"error": "Slot unavailable! Another follow-up is already scheduled for this time."}, status=400)

        # Save inside a transaction block
        with transaction.atomic():
            followup = serializer.save(follower=salesmanager, lead=lead)

            def enqueue_notifications():
                
                send_followup_notifications.apply_async(
                    args=[followup.id, "30_min"],
                    eta=localtime(followup.followup_date) - timedelta(minutes=30)
                )

            transaction.on_commit(enqueue_notifications)

        return Response({"message": "Follow-Up scheduled successfully", "data": serializer.data}, status=201)

    return Response(serializer.errors, status=400)


    

    
    
    

@api_view(["GET"])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def list_followups(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()

    followups = FollowUp.objects.filter(follower_id=salesmanager.id).values("lead__name", "followup_date")
    return Response({"followups": list(followups)}, status=200)



@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def edit_followup(request, followup_id):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()

    try:
        followup = FollowUp.objects.get(id=followup_id)
    except FollowUp.DoesNotExist:
        return Response({"error": "Follow-Up not found"}, status=status.HTTP_404_NOT_FOUND)

    if followup.follower.id != salesmanager.id:
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    # time_difference = followup.followup_date - now()
    # if time_difference.total_seconds() < 3600:  # Less than 1 hour remaining
    #     return Response({"error": "Follow-Up cannot be edited within 1 hour of the scheduled time"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = FollowUpSerializer(followup, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Follow-Up updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def cancel_followup(request, followup_id):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()

    try:
        followup = FollowUp.objects.get(id=followup_id)
    except FollowUp.DoesNotExist:
        return Response({"error": "Follow-Up not found"}, status=status.HTTP_404_NOT_FOUND)

    if followup.follower.id != salesmanager.id:
        return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    # time_difference = followup.followup_date - now()
    # if time_difference.total_seconds() < 1800:  
    #     return Response({"error": "Follow-Up cannot be canceled within 30 minutes of the scheduled time"}, status=status.HTTP_400_BAD_REQUEST)

    followup.delete()
    return Response({"message": "Follow-Up canceled successfully"}, status=status.HTTP_200_OK)





@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def followup_status_entry(request, followup_id):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    try:
        followup = FollowUp.objects.get(id=followup_id,follower = salesmanager)
    except FollowUp.DoesNotExist:
        return Response({"error": "Follow-up not found."}, status=status.HTTP_404_NOT_FOUND)

    # Check if the followup already has a status
    try:
        existing_status = Followup_status.objects.get(followup=followup)
    except Followup_status.DoesNotExist:
        existing_status = None

    serializer = FollowupStatusSerializer(instance=existing_status, data=request.data)

    if serializer.is_valid():
        serializer.save(followup=followup)
        return Response(serializer.data, status=status.HTTP_200_OK if existing_status else status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










#react l polling use cheyanam 5 min intervels
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def get_followup_reminders(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()

    current_time = now()
    local_current_time = localtime(current_time)
    reminder_time = local_current_time + timedelta(minutes=5)  # Follow-ups happening in 5 minutes

    

    upcoming_followups = FollowUp.objects.filter(
        follower_id=salesmanager.id,
        followup_date__gte=local_current_time,
        followup_date__lte=reminder_time
    ).values("id", "followup_date", "notes")
    upcoming_events = Sales_Manager_Event.objects.filter(
        staff=salesmanager,
        date_time__gte = local_current_time,
        date_time__lte = reminder_time
    ).values("id","date_time","event_name","priority","notes")

    notifications = [
        {
            "message": f"⏳ Reminder: Your follow-up is in 5 minutes at {localtime(followup['followup_date']).strftime('%Y-%m-%d %H:%M')}. Notes: {followup['notes']}"
        }
        for followup in upcoming_followups
    ]
    event_notifications = [
        {
            "type": "event",
            "message": f"📅 Event Alert: '{e['event_name']}' is scheduled in 5 minutes at {localtime(e['date_time']).strftime('%Y-%m-%d %H:%M')}. Priority: {e['priority']}. Notes: {e['notes']}"
        }
        for e in upcoming_events
    ]
    notifications = notifications + event_notifications

    return Response({
        "notifications": notifications,
        "time": local_current_time
    })




@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def salesmanager_today_upcoming_events(request):
    staff = request.user

    # ✅ Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, "sales_manager_reg"):
        return Response({"error": "Not a valid sales manager"}, status=403)

    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()

    if not salesmanager:
        return Response({"error": "Sales manager not found"}, status=404)
    current_time = localtime(now())
    # ✅ Get today's start and end date with correct timezone handling
    today_start = localtime(now()).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = localtime(now()).replace(hour=23, minute=59, second=59, microsecond=999999)

    # ✅ Get today's follow-ups for the sales manager
    followups = FollowUp.objects.filter(
        follower_id=salesmanager.id,
        followup_date__gte=current_time,
    )

    # ✅ Get today's events for the sales manager
    events = Sales_Manager_Event.objects.filter(
        staff_id=salesmanager.id,
        date_time__gte=today_start,
    )

    # ✅ Debugging Logs (Optional - Remove Later)
    

    

    # ✅ Serialize follow-ups and events
    followup_data = FollowUpWithCustomerSerializer(followups, many=True).data
    event_data = SalesManagerEventSerializer(events, many=True).data

    # ✅ Return combined response
    return Response(
        {
            "followups": followup_data,
            "events": event_data,
        },
        status=status.HTTP_200_OK,
    )
    
    
    
@api_view(["GET"])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def salesmanager_all_events(request):
    staff = request.user

    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()


    all_followups = FollowUp.objects.filter(follower_id=salesmanager.id)
    

    # Fix for FollowUp filtering
    

    all_events = Sales_Manager_Event.objects.filter(staff_id=salesmanager.id)
    


    return Response(
        {
            "followups": FollowUpWithCustomerSerializer(all_followups, many=True).data,
            "events": Sales_Manager_EventSerializer(all_events, many=True).data,
        },
        status=status.HTTP_200_OK,
    )
    
    
    
    
    

@api_view(["GET"])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def leadwise_followups(request,lead_id):
    staff = request.user

    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.filter(user=staff.id).first()
    followups= FollowUp.objects.filter(lead=lead_id,follower=salesmanager)
    serializer=FollowUpSerializer(followups,many=True).data 
    return Response(serializer,status=status.HTTP_200_OK)