from django.db import models
from databank_section.models import DataBank
from django.utils import timezone

# Create your models here.
class Project_db(models.Model):
    project_icon = models.ImageField(upload_to="project_icons",null=True)
    project_name = models.CharField(max_length=200,default="test_project",unique=True)
    data_bank = models.ManyToManyField(DataBank,related_name="projects")
    importance = models.CharField(max_length=100)
    start_date = models.DateField()
    time_stamp = models.DateTimeField(default=timezone.now)
    deadline = models.DateField()
    description = models.CharField(max_length=200)