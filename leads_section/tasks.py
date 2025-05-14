from celery import shared_task
from django.core.mail import send_mail
from datetime import datetime
from .models import Leads  # Import your Lead model

@shared_task
def send_followup_email(lead_id):
    lead = Leads.objects.filter(id=lead_id).first()
    if lead:
        subject = "Follow-Up: Lead Closure Notification"
        message = f"Dear {lead.name},\n\nYour lead was closed one year ago. If you need further assistance, feel free to reach out.\n\nBest regards,\nYour Company"
        recipient_email = lead.email  # Assuming you have customer_email field
        send_mail(subject, message, 'jrdjangodeveloper@gmail.com', [recipient_email])