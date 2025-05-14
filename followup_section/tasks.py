from celery import shared_task
from celery.exceptions import Retry
from django.core.mail import send_mail
from .models import FollowUp
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils.timezone import localtime, make_aware
from django.utils import timezone
import time
import sys

@shared_task(bind=True, max_retries=5, default_retry_delay=3)  # retry up to 5 times with 3 seconds delay
def send_followup_notifications(self, followup_id, notification_type):
    try:
        time.sleep(5)
        followup = FollowUp.objects.get(id=followup_id)
        followup_date = followup.followup_date

        # Ensure timezone-aware
        if timezone.is_naive(followup_date):
            followup_date = make_aware(followup_date)
        followup_date_local = localtime(followup_date)

        client_email = followup.lead.email
        staff_email = followup.follower.email
        staff_id = followup.follower.id

        # Get the names of the lead and the sales manager
        client_name = followup.lead.name  # Assuming `name` field in Leads model holds full name
        staff_name = followup.follower.username# Using first and last name of the sales manager

        # Notification content for client
        if notification_type == "created":
            subject_client = "Follow-Up Scheduled"
            message_client = (
                f"Dear {client_name},\n\n"
                f"We would like to inform you that a follow-up has been scheduled with our Sales Manager, {staff_name}, on {followup_date_local.strftime('%Y-%m-%d %H:%M')}.\n\n"
                f"Please be prepared for the follow-up session at the scheduled time.\n\n"
                f"Best regards,\n"
                f"Devlok CRM Team"
            )
        elif notification_type == "24_hour":
            subject_client = "Reminder: Follow-Up Tomorrow"
            message_client = (
                f"Dear {client_name},\n\n"
                f"This is a friendly reminder that your follow-up with our Sales Manager, {staff_name}, is scheduled for tomorrow at {followup_date_local.strftime('%Y-%m-%d %H:%M')}.\n\n"
                f"Please be available at the scheduled time.\n\n"
                f"Best regards,\n"
                f"Devlok CRM Team"
            )
        elif notification_type == "30_min":
            subject_client = "Reminder: Follow-Up in 30 Minutes"
            message_client = (
                f"Dear {client_name},\n\n"
                f"This is a final reminder that your follow-up with our Sales Manager, {staff_name}, is scheduled in 30 minutes at {followup_date_local.strftime('%Y-%m-%d %H:%M')}.\n\n"
                f"Please make sure to be available at the scheduled time.\n\n"
                f"Best regards,\n"
                f"Devlok CRM Team"
            )

        # Notification content for sales manager (staff)
        if notification_type == "created":
            subject_staff = "Follow-Up Scheduled"
            message_staff = (
                f"Dear {staff_name},\n\n"
                f"A follow-up has been scheduled with your client, {client_name}, on {followup_date_local.strftime('%Y-%m-%d %H:%M')}.\n\n"
                f"Please ensure you are prepared for the session.\n\n"
                f"Best regards,\n"
                f"Devlok CRM Team"
            )
        elif notification_type == "24_hour":
            subject_staff = "Reminder: Follow-Up Tomorrow"
            message_staff = (
                f"Dear {staff_name},\n\n"
                f"Reminder: Your follow-up with your client, {client_name}, is scheduled for tomorrow at {followup_date_local.strftime('%Y-%m-%d %H:%M')}.\n\n"
                f"Please be prepared for the session.\n\n"
                f"Best regards,\n"
                f"Devlok CRM Team"
            )
        elif notification_type == "30_min":
            subject_staff = "Reminder: Follow-Up in 30 Minutes"
            message_staff = (
                f"Dear {staff_name},\n\n"
                f"Final reminder: Your follow-up with your client, {client_name}, is scheduled in 30 minutes at {followup_date_local.strftime('%Y-%m-%d %H:%M')}.\n\n"
                f"Please ensure you are ready for the session.\n\n"
                f"Best regards,\n"
                f"Devlok CRM Team"
            )

        # Send email to both client and sales manager with their respective content
        send_mail(
            subject_client, 
            message_client, 
            "suryakrishnavaliyapurakkal@gmail.com", 
            [client_email],  # Send only to the client
            fail_silently=False
        )
        send_mail(
            subject_staff, 
            message_staff, 
            "suryakrishnavaliyapurakkal@gmail.com", 
            [staff_email],  # Send only to the sales manager
            fail_silently=False
        )
        
        print(f"✅ Email sent to {client_email} and {staff_email}")

        # WebSocket or other notifications can be handled here if needed
        # Example: async_to_sync(get_channel_layer().send)(f"user_{staff_id}", {
        #     "type": "notification",
        #     "message": message_staff
        # })

    except FollowUp.DoesNotExist:
        print(f"❌ Follow-up not found, retrying... (ID: {followup_id})")
        raise self.retry(exc=FollowUp.DoesNotExist(f"FollowUp {followup_id} not found"), countdown=2)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise self.retry(exc=e, countdown=5)

    finally:
        sys.stdout.flush()