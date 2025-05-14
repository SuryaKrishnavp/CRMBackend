from django.db import models
from django.utils import timezone
from leads_section.models import Leads
from auth_section.models import Sales_manager_reg

class DataBank(models.Model):
    lead = models.ForeignKey(Leads,on_delete=models.CASCADE,related_name='databank_lead')
    timestamp = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True)
    phonenumber = models.CharField(max_length=15)
    district = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    address = models.CharField(max_length=100,default="Address")
    PURPOSE_CHOICES = [
        ('For Selling a Property','for selling a property'),
        ('For Buying a Property','for buying a property'),
        ('For Rental or Lease','for rental or lease'),
        ('Looking to Rent or Lease Property','looking to rent or lease')
    ]
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES)
    
    mode_of_property = models.CharField(max_length=100)
    demand_price = models.IntegerField()
    location_proposal_district = models.CharField(max_length=150,null=True,blank=True)
    location_proposal_place = models.CharField(max_length=150,null=True,blank=True)
    area_in_sqft = models.CharField(max_length=100)
    building_roof = models.CharField(max_length=100,null=True,blank=True)
    number_of_floors = models.IntegerField(null=True,blank=True)
    building_bhk = models.IntegerField(null=True,blank=True)
    additional_note = models.CharField(max_length=250,null=True,blank=True)
    follower = models.ForeignKey(Sales_manager_reg,on_delete=models.CASCADE)
    location_link = models.CharField(max_length=500, null=True, blank=True)
    lead_category = models.CharField(max_length=200)
    image_folder = models.CharField(max_length=100,null=True,blank=True)
    
    
    
class DataBankImage(models.Model):
    databank = models.ForeignKey(DataBank, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='databank_photos/')

    def __str__(self):
        return f"Image for {self.databank.name}"