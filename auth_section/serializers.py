from rest_framework import serializers
from .models import Admin_reg,Sales_manager_reg,Ground_level_managers_reg

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
        
class SalesmanLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales_manager_reg
        fields = 'email','password'
        
        

        
from django.contrib.auth.models import User  # Import User model for creating the user

class AddSalesManagerSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False)

    class Meta:
        model = Sales_manager_reg
        fields = ['id','username', 'email', 'phonenumber', 'password', 'photo']

    def create(self, validated_data):
        # Extract password and user fields separately if needed
        password = validated_data.pop('password', None)
        user_instance = validated_data.pop('user', None)  # Get the User instance

        # If no user instance is provided, create one using the provided validated data
        if not user_instance:
            user_instance = User.objects.create_user(
                username=validated_data.get('username'),
                email=validated_data.get('email'),
                password=password
            )

        # Make sure that this user is not already linked to another Sales Manager
        if Sales_manager_reg.objects.filter(user=user_instance).exists():
            raise serializers.ValidationError({"user": "This user is already linked to another sales manager."})

        # Create the Sales Manager instance and link it to the user
        sales_manager = Sales_manager_reg(**validated_data)

        # If a password is provided, set it for the sales manager (hashed password)
        if password:
            sales_manager.set_password(password)

        # Link the Sales Manager to the provided or newly created User instance
        sales_manager.user = user_instance
        
        # Save the instance to the database
        sales_manager.save()

        return sales_manager
        
class AdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin_reg
        fields = ["username", "email", "phonenumber", "password"]  

class Add_GLM_Serializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False)
    class Meta:
        model = Ground_level_managers_reg
        fields = "__all__"
        
class Get_Admin_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Admin_reg
        fields = ["username", "email", "phonenumber"]
        
        
class GetSalesManagerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # If you want to allow password changes
    
    class Meta:
        model = Sales_manager_reg
        fields = '__all__'  # Include all fields, including password
    
    def to_representation(self, instance):
        """
        Override the default to_representation method to include the plain password.
        This should be used with caution!
        """
        representation = super().to_representation(instance)
        
        # You could expose the plain password here, but this is a security risk.
        representation['password'] = instance.password  # Assuming password is stored as plain text
        
        return representation
    
    
class AddAdminSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False)

    class Meta:
        model = Admin_reg
        fields = ['username', 'email', 'phonenumber', 'password', 'photo']

    def create(self, validated_data):
        # Extract password and user fields separately
        password = validated_data.pop('password', None)

        # If no user instance is provided, create one using the validated data
        user_instance = validated_data.pop('user', None)  # User is part of Admin_reg
        if not user_instance:
            user_instance = User.objects.create_user(
                username=validated_data.get('username'),
                email=validated_data.get('email'),
                password=password
            )

        # Create the Admin instance and link it to the user
        admin = Admin_reg(**validated_data)
        
        # If a password is provided, hash and set it for the admin
        if password:
            admin.set_password(password)

        # Link the Admin instance to the User instance
        admin.user = user_instance
        
        # Save the admin instance to the database
        admin.save()

        return admin