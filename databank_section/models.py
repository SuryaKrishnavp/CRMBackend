from django.db import models
from django.utils import timezone
from leads_section.models import Leads
from auth_section.models import Sales_manager_reg

class DataBank(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100)
    phonenumber = models.CharField(max_length=15)
    district = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    location_preferences = models.CharField(max_length=500,null=True,blank=True)
    address = models.CharField(max_length=100,null=True,blank=True)
    PURPOSE_CHOICES = [
        ('For Selling a Property','for selling a property'),
        ('For Buying a Property','for buying a property'),
        ('For Rental or Lease','for rental or lease'),
        ('Looking to Rent or Lease Property','looking to rent or lease')
    ]
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    mode_of_property = models.CharField(max_length=100)
    demand_price = models.IntegerField(null=True,blank=True)
    advance_price = models.IntegerField(null=True,blank=True)
    area_in_sqft = models.CharField(max_length=100,null=True,blank=True)
    area_in_cent = models.CharField(max_length=100,null=True,blank=True)
    building_roof = models.CharField(max_length=100,null=True,blank=True)
    number_of_floors = models.CharField(null=True,blank=True)
    building_bhk = models.CharField(null=True,blank=True)
    additional_note = models.CharField(max_length=250,null=True,blank=True)
    location_link = models.CharField(max_length=500, null=True, blank=True)
    lead_category = models.CharField(max_length=200)
    image_folder = models.CharField(max_length=100,null=True,blank=True)
    status = models.CharField(max_length = 100,default="Pending")
    stage = models.CharField(max_length=100,default="Not Opened")
    closed_date = models.DateField(null=True,blank=True)
    


class LeadDataFollower(models.Model):
    lead = models.ForeignKey(DataBank,on_delete=models.CASCADE)
    follower = models.ForeignKey(Sales_manager_reg,on_delete=models.CASCADE)
    
    
    
class DataBankImage(models.Model):
    databank = models.ForeignKey(DataBank, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='databank_photos/')

    def __str__(self):
        return f"Image for {self.databank.name}"
    
    
    
    
    
    
