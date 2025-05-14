from rest_framework import serializers
from .models import FollowUp,Followup_status




class FollowupStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Followup_status
        fields = ['status', 'note']



class FollowUpSerializer(serializers.ModelSerializer):
    followup_status = serializers.SerializerMethodField()

    class Meta:
        model = FollowUp
        fields = ["id", "followup_date", "notes", "followup_status"]

    def get_followup_status(self, obj):
        status = Followup_status.objects.filter(followup=obj).first()
        if status:
            return FollowupStatusSerializer(status).data
        return None



class FollowUpWithCustomerSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="lead.name", read_only=True)
    purpose = serializers.CharField(source="lead.purpose", read_only=True)
    followup_status = serializers.SerializerMethodField()

    class Meta:
        model = FollowUp
        fields = ["id", "followup_date", "notes", "customer_name", "purpose", "followup_status"]

    def get_followup_status(self, obj):
        try:
            followup_status = Followup_status.objects.get(followup=obj)
            return {
                "status": followup_status.status,
                "note": followup_status.note
            }
        except Followup_status.DoesNotExist:
            return {
                "status": "Pending",
                "note": ""
            }


        
        
        
class FollowupStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Followup_status
        fields = ['id', 'followup', 'status', 'note']
        read_only_fields = ['followup'] 