from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
import uuid
from django.utils.timezone import now, timedelta
from django.utils import timezone
from django.contrib.auth.models import User


# Create your models here.
class AbstractUser(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phonenumber = models.CharField(max_length=15, unique=True)
    password = models.CharField(max_length=128)  # This will be used only by Admin and Sales Manager
    photo = models.ImageField(null=True, blank=True)

    class Meta:
        abstract = True

    def set_password(self, raw_password):
        """Override this method to hash and set the password"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Override this method to check hashed password"""
        return check_password(raw_password, self.password)

    def generate_reset_token(self):
        """Generate a secure reset token and set expiry time (e.g., 15 minutes)"""
        self.reset_token = str(uuid.uuid4())  
        self.token_expiry = now() + timedelta(minutes=15)
        self.save()
        return self.reset_token

    def get_jwt_token(self):
        """Generate JWT Token for user authentication"""
        # This method assumes you are using django-rest-framework-simplejwt or a similar library
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self)
        return str(refresh.access_token)

# Admin model inheriting from the abstract base class
class Admin_reg(AbstractUser):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Link to Django User model

    is_staff = models.BooleanField(default=True)
    reset_token = models.CharField(max_length=100, blank=True, null=True, unique=True)
    token_expiry = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure the password is hashed before saving
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)  # Hash the password before saving it
        if Admin_reg.objects.exists() and not self.pk:  
            raise ValidationError("Only one admin record is allowed.")
        self.is_staff = True  # Admin must always have is_staff as True
        super().save(*args, **kwargs)

    def get_jwt_token(self):
        """Generate JWT Token for admin authentication"""
        return super().get_jwt_token()

# Sales Manager model inheriting from the abstract base class
class Sales_manager_reg(AbstractUser):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_sales_manager = models.BooleanField(default=True)
    joined_by = models.DateField(default=timezone.now)

    def get_jwt_token(self):
        """Generate JWT Token for sales manager authentication"""
        return super().get_jwt_token()
    

class Ground_level_managers_reg(models.Model):
    joined_by = models.DateField(default=timezone.localdate)
    photo = models.ImageField(upload_to='groundlevelmanagers_photos/',null=True,blank=True)
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phonenumber = models.CharField(max_length=15,unique=True)
    
    
