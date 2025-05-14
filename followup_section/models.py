from django.db import models
from leads_section.models import Leads
from auth_section.models import Sales_manager_reg
import datetime
from datetime import timedelta
from django.utils.timezone import now
from django.utils import timezone
import pytz


# Create your models here.
class FollowUp(models.Model):
    lead = models.ForeignKey(Leads, on_delete=models.CASCADE)
    follower = models.ForeignKey(Sales_manager_reg, on_delete=models.CASCADE)
    followup_date = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ("follower", "lead", "followup_date")
        
        
    def can_edit_or_cancel(self):
        """ Restrict edits and cancellations within 24 hours before the follow-up date """
        edit_deadline = self.followup_date - timedelta(hours=24)
        return now() < edit_deadline
    
    
    
class Followup_status(models.Model):
    followup = models.ForeignKey(FollowUp,on_delete=models.CASCADE)
    status = models.CharField(max_length=100)
    note = models.CharField(max_length=200)
    