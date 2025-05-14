from django.db import models
from auth_section.models import Sales_manager_reg
# Create your models here.

class Admin_event_list(models.Model):
    event_name = models.CharField(max_length=100,null=True)
    date_time = models.DateTimeField(unique=True)
    priority = models.CharField(max_length=100)
    notes = models.CharField(max_length=150)
    
    
    
class Admin_Event_Status(models.Model):
    admin_event = models.ForeignKey(Admin_event_list,on_delete=models.CASCADE)
    status = models.CharField(max_length=100)
    note = models.CharField(max_length=200)


class Sales_Manager_Event(models.Model):
    staff = models.ForeignKey(Sales_manager_reg,on_delete=models.CASCADE)
    event_name = models.CharField(max_length=100,null=True)
    date_time = models.DateTimeField()
    priority = models.CharField(max_length=100)
    notes = models.CharField(max_length=150)
    
    class Meta:
        unique_together = ("staff", "date_time")
    
    
class Sales_manager_Event_Status(models.Model):
    event = models.ForeignKey(Sales_Manager_Event,on_delete=models.CASCADE)
    status = models.CharField(max_length=100)
    note = models.CharField(max_length=200)