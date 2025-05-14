from rest_framework import serializers
from .models import Project_db
from databank_section.models import DataBank
 
        
class DataBankProjectSerializer(serializers.ModelSerializer):
    follower = serializers.CharField(source='follower.username', default="Unknown", read_only=True)  
    class Meta:
        model = DataBank
        exclude = ['lead']
        
class ProjectSerializer(serializers.ModelSerializer):
    data_bank = DataBankProjectSerializer(many=True, read_only=True)
    class Meta:
        model = Project_db
        fields = "__all__"
        
class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project_db
        fields = ['project_icon', 'project_name', 'importance', 'deadline','start_date','description']

    def create(self, validated_data):
        # Create project without data_bank initially
        return Project_db.objects.create(**validated_data)
        
        
class AddDataBankSerializer(serializers.Serializer):
    data_bank_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_data_bank_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one DataBank ID is required.")
        
        # Check if any DataBank is already linked to another project
        conflicting_data_banks = DataBank.objects.filter(id__in=value, projects__isnull=False).distinct()

        if conflicting_data_banks.exists():
            conflicting_ids = list(conflicting_data_banks.values_list('id', flat=True))
            raise serializers.ValidationError(
                f"DataBanks {conflicting_ids} are already linked to another project. Cannot link them to a new project."
            )

        return value
    
class RemoveDataBankSerializer(serializers.Serializer):
    data_bank_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_data_bank_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one DataBank ID is required.")

        # Check if DataBanks exist
        existing_data_banks = DataBank.objects.filter(id__in=value)

        if not existing_data_banks.exists():
            raise serializers.ValidationError(
                f"No matching DataBanks found with IDs {value}."
            )

        return value
    
    
class ProjectEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project_db
        fields = ['project_icon', 'project_name', 'importance', 'deadline','description']

    def validate_importance(self, value):
        valid_importance_levels = ['High', 'Medium', 'Low']

        if value not in valid_importance_levels:
            raise serializers.ValidationError("Importance should be either High, Medium, or Low.")

        return value
    
    
    
