from rest_framework.permissions import BasePermission
from .models import Admin_reg,Sales_manager_reg
from rest_framework import permissions

class IsCustomAdminUser(permissions.BasePermission):
    """
    Custom permission to allow only users from Admin_reg who have is_staff=True.
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated and is an Admin with is_staff=True
        if request.user.is_authenticated:
            try:
                # Check if the user has an associated Admin object and is_staff is True
                user = Admin_reg.objects.get(user=request.user)
                return user.is_staff  # Only allow access if the user is staff (admin)
            except Admin_reg.DoesNotExist:
                return False  # If no Admin object is found, deny access
        return False  # If the user is not authenticated, deny access

class IsSalesManagerUser(permissions.BasePermission):
    """
    Custom permission to allow only users who are Sales Managers (checking `is_sales_manager`).
    """
    def has_permission(self, request, view):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            print(f"Authenticated user: {request.user}")  # Debugging line
            
            try:
                # Retrieve the Sales_manager_reg object related to the user
                sales_manager = Sales_manager_reg.objects.get(user=request.user)
                print(f"Sales Manager: {sales_manager}")  # Debugging line
                
                # Check if the user is a Sales Manager by the `is_sales_manager` field
                if sales_manager.is_sales_manager:
                    return True  # Allow access if `is_sales_manager` is True
                else:
                    print("User is not a sales manager")  # Debugging line
                    return False  # Deny access if `is_sales_manager` is False
            except Sales_manager_reg.DoesNotExist:
                print("Sales Manager record does not exist for user")  # Debugging line
                return False  # Deny access if the user doesn't have a Sales Manager record
        else:
            print("User is not authenticated")  # Debugging line
            return False  # Deny access if the user is not authenticated