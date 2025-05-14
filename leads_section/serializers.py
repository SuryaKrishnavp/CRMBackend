from .models import Leads,LeadCategory
from rest_framework import serializers
from auth_section.models import Sales_manager_reg






class LeadCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadCategory
        fields = "__all__"



class LeadsViewSerializer(serializers.ModelSerializer):
    lead_category = LeadCategorySerializer(many=True, read_only=True)
    follower_name = serializers.SerializerMethodField()

    class Meta:
        model = Leads
        fields = '__all__'  # or list fields explicitly if needed
        # Example: fields = ['id', 'name', ..., 'follower_name']

    def get_follower_name(self, obj):
        try:
            sales_manager = Sales_manager_reg.objects.get(id=obj.staff_id)
            return sales_manager.user.username
        except Sales_manager_reg.DoesNotExist:
            return None
        except Exception:
            return None

        
class EnterLeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        exclude = ['follower','staff_id']
        
        
        
class AdminEnterLeadsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leads
        fields = "__all__"