from django.contrib import admin
from .models import Admin_reg,Sales_manager_reg,Ground_level_managers_reg

admin.site.register(Sales_manager_reg)
admin.site.register(Ground_level_managers_reg)

from django.contrib.auth.hashers import make_password


@admin.register(Admin_reg)
class AdminRegAdmin(admin.ModelAdmin):
    
    def save_model(self, request, obj, form, change):
        if 'password' in form.changed_data:  # Only hash password if it was changed
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)

