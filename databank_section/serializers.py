from rest_framework import serializers
from .models import DataBank,DataBankImage

class DatabankSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBank
        exclude = ['lead','follower']  # This removes 'lead' from required fields

    
    
class DataBankEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBank
        fields = '__all__' 
        
        
        
class DataBankGETSerializer(serializers.ModelSerializer):
    follower_name = serializers.CharField(source='follower.username', read_only=True)
    is_in_project = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = DataBank
        fields = '__all__'
        extra_fields = ['is_in_project', 'project_name']

    def get_is_in_project(self, obj):
        return obj.projects.exists()

    def get_project_name(self, obj):
        first_project = obj.projects.first()
        return first_project.project_name if first_project else None

        
class DataBankImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBankImage
        fields = ['id', 'image']