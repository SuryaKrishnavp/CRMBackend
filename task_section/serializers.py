from rest_framework import serializers
from .models import Admin_event_list,Sales_Manager_Event,Sales_manager_Event_Status,Admin_Event_Status
from django.utils.timezone import make_aware
from followup_section.models import FollowUp

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin_event_list
        fields = '__all__'

    def validate_date_time(self, value):
        if value.tzinfo is None:
            value = make_aware(value)

        event_id = self.instance.id if self.instance else None
        if Admin_event_list.objects.exclude(id=event_id).filter(date_time=value).exists():
            raise serializers.ValidationError("This time slot is already booked. Please choose another time.")
        
        return value
    
    
    
class AdminEventStatusInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin_Event_Status
        fields = ['status', 'note']


class AdminEventListWithStatusSerializer(serializers.ModelSerializer):
    event_status = serializers.SerializerMethodField()

    class Meta:
        model = Admin_event_list
        fields = ['id', 'event_name', 'date_time', 'priority', 'notes', 'event_status']

    def get_event_status(self, obj):
        try:
            status_obj = Admin_Event_Status.objects.get(admin_event=obj)
            return AdminEventStatusInlineSerializer(status_obj).data
        except Admin_Event_Status.DoesNotExist:
            return None

    
    

class AdminEventStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin_Event_Status
        fields = ['id', 'admin_event', 'status', 'note']
        read_only_fields = ['admin_event'] 
    
    
class Sales_Manager_EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales_Manager_Event
        fields = '__all__'

    def validate_date_time(self, value):
        if value.tzinfo is None:
            value = make_aware(value)

        event_id = self.instance.id if self.instance else None
        if Admin_event_list.objects.exclude(id=event_id).filter(date_time=value).exists():
            raise serializers.ValidationError("This time slot is already booked. Please choose another time.")
        
        return value
    
    
    
    
    
class SalesManagerEventSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    event_status = serializers.SerializerMethodField()

    class Meta:
        model = Sales_Manager_Event
        fields = ["id", "event_name", "date_time", "priority", "notes", "staff_name", "event_status"]

    def get_event_status(self, obj):
        try:
            status_obj = Sales_manager_Event_Status.objects.get(event=obj)
            return {
                "status": status_obj.status,
                "note": status_obj.note
            }
        except Sales_manager_Event_Status.DoesNotExist:
            return {
                "status": "Pending",
                "note": ""
            }


class FollowUpSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source="lead.name", read_only=True)
    follower_name = serializers.CharField(source="follower.name", read_only=True)

    class Meta:
        model = FollowUp
        fields = ["lead_name", "follower_name", "followup_date", "notes"]



class AdminEventListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin_event_list
        fields = "__all__"
        
        
        
        
class EventStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales_manager_Event_Status
        fields = ['id', 'event', 'status', 'note']
        read_only_fields = ['event'] 