from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from .permissions import IsCustomAdminUser,IsSalesManagerUser
from rest_framework.response import Response
from .serializers import LoginSerializer,GetSalesManagerSerializer,AddSalesManagerSerializer,AdminUpdateSerializer,Add_GLM_Serializer,Get_Admin_Serializer,AddAdminSerializer
from .models import Admin_reg,Sales_manager_reg,Ground_level_managers_reg
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from rest_framework import status
from django.middleware.csrf import get_token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
import time
from django.core.cache import cache


# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def create_admin(request):
    serializer = AddAdminSerializer(data=request.data)
    
    if serializer.is_valid():
        # Save the admin instance using the serializer
        admin = serializer.save()

        # Optionally send a confirmation email or return relevant data
        response_data = {
            "message": "Admin created successfully!",
            "username": admin.username,
            "email": admin.email
        }

        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def get_admin(request):
    admins = Admin_reg.objects.only('username', 'email', 'phonenumber')
    data = list(admins.values('username', 'email', 'phonenumber'))
    return Response(data, status=200)



@api_view(['POST'])
@permission_classes([AllowAny])
def Login_func(request):
    start_time = time.time()  # ⏱️ Start measuring

    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        # Check Admin
        admin_user = Admin_reg.objects.select_related('user').filter(email=email).first()
        if admin_user and check_password(password, admin_user.password):
            refresh = RefreshToken.for_user(admin_user.user)
            response = {
                "message": "Admin successfully logged in",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "username": admin_user.username,
                "id": admin_user.user.id,
            }
            print("Login duration:", time.time() - start_time)
            return Response(response, status=200)

        # Check Sales Manager
        sales_manager_user = Sales_manager_reg.objects.select_related('user').filter(email=email).first()
        if sales_manager_user and check_password(password, sales_manager_user.password):
            refresh = RefreshToken.for_user(sales_manager_user.user)
            response = {
                "message": "Sales Manager successfully logged in",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "username": sales_manager_user.username,
                "id": sales_manager_user.id,
            }
            print("Login duration:", time.time() - start_time)
            return Response(response, status=200)

        print("Login duration:", time.time() - start_time)
        return Response({"error": "Invalid credentials"}, status=400)

    print("Login duration:", time.time() - start_time)
    return Response({"error": "Invalid data"}, status=400)







@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])  # Check that the user is authenticated and is an admin
def Add_Salesman(request):
    # Extract the authenticated user (admin) from the JWT token
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    # Initialize the serializer to add a new sales manager
    serializer = AddSalesManagerSerializer(data=request.data)

    if serializer.is_valid():
        password = serializer.validated_data.get('password')
        # Save the sales manager data
        serializer.save()

        # Get the saved instance of the sales manager
        sales_manager = serializer.instance

        # Send a confirmation email
        subject = "Your Account has been Created"
        message = f"Hello {sales_manager.username},\n\nYour account has been successfully created!\n\nEmail: {sales_manager.email}\nPassword: {password}\n\nLogin and update your password for security."
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [sales_manager.email]

        send_mail(subject, message, from_email, recipient_list)

        return Response({"message": "Salesman added and email sent successfully!"}, status=201)

    return Response(serializer.errors, status=400)
        
        
        
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsCustomAdminUser])
def Update_Salesman(request, salesmanager_id):
    admin = request.user

    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        sales_manager = Sales_manager_reg.objects.get(id=salesmanager_id)
    except Sales_manager_reg.DoesNotExist:
        return Response({'error': 'Sales Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    # Save current username to check for change later
    old_username = sales_manager.user.username

    serializer = AddSalesManagerSerializer(sales_manager, data=request.data, partial=True)

    if serializer.is_valid():
        # Get validated fields manually
        validated_data = serializer.validated_data
        new_username = validated_data.get('username')

        # Save serializer (other fields)
        serializer.save()

        user = sales_manager.user

        if new_username and old_username != new_username:
            user.username = new_username

        

        user.save()

        # Update leads with new follower username
        if new_username and old_username != new_username:
            from leads_section.models import Leads
            Leads.objects.filter(follower=old_username).update(follower=new_username)

        return Response({
            "message": "Sales Manager details updated successfully!",
            "data": serializer.data
        }, status=200)

    return Response(serializer.errors, status=400)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def update_sales_manager_password(request, salesmanager_id):
    admin = request.user

    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        sales_manager = Sales_manager_reg.objects.get(id=salesmanager_id)
    except Sales_manager_reg.DoesNotExist:
        return Response({'error': 'Sales Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    new_password = request.data.get('password')

    if not new_password:
        return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

    # Use your custom method to hash the password
    sales_manager.set_password(new_password)
    sales_manager.save()

    return Response({'message': 'Password updated successfully!'}, status=status.HTTP_200_OK)
                
            
            
@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')

    user = Admin_reg.objects.filter(email=email).first() 
    if not user:
        return Response({"error": "Sales Managers can't update password,Contact Admin!"}, status=404)

    reset_token = user.generate_reset_token()

    reset_link = f"https://devlokcrm.up.railway.app/reset-password/{reset_token}/"

    subject = "Password Reset Request"
    message = f"Click the link below to reset your password:\n{reset_link}\nThis link will expire in 15 minutes."
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, from_email, recipient_list)
    return Response({"message": "Password reset link sent to email"}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request, token):
    new_password = request.data.get('new_password')

    admin_user = Admin_reg.objects.filter(reset_token=token).first()
    user = admin_user   

    if not user or now() > user.token_expiry:
        return Response({"error": "Invalid or expired token"}, status=400)

    user.password = make_password(new_password)  
    user.reset_token = None  
    user.token_expiry = None
    user.save()

    return Response({"message": "Password reset successful"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def SalesManager_details(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    
    if request.method == 'GET':
        data = Sales_manager_reg.objects.all()
        serializer = GetSalesManagerSerializer(data, many=True)  
        return Response(serializer.data)
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def delete_sales_manager(request, sales_manager_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        sales_manager = Sales_manager_reg.objects.get(id=sales_manager_id)
        sales_manager.delete()
        return Response({'message': 'Sales Manager deleted successfully'}, status=status.HTTP_200_OK)
    except Sales_manager_reg.DoesNotExist:
        return Response({'error': 'Sales Manager not found'}, status=status.HTTP_404_NOT_FOUND)
            
            


@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])  
def update_admin(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)

    if not admin:  # If admin does not exist in DB
        return Response({'error': 'Invalid admin user'}, status=status.HTTP_403_FORBIDDEN)
    try:
        admin = Admin_reg.objects.first()  
        if not admin:
            return Response({"error": "Admin record not found"}, status=404)

        serializer = AdminUpdateSerializer(admin, data=request.data, partial=True)
        if serializer.is_valid():
            updated_fields = []
            
            if "password" in serializer.validated_data:
                admin.set_password(serializer.validated_data["password"])  
                serializer.validated_data.pop("password")  
                updated_fields.append("Password")

            serializer.save()
            
            updated_fields.extend(serializer.validated_data.keys())  
            updated_fields = ', '.join(updated_fields) if updated_fields else "No changes"

            subject = "Your Admin Account Details Updated"
            message = f"Hello {admin.username},\n\nYour account details have been successfully updated.\n\nUpdated Fields: {updated_fields}\n\nIf you did not request this change, please contact support immediately."
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [admin.email]

            send_mail(subject, message, from_email, recipient_list)

            return Response({"message": "Admin details updated successfully, and email sent"}, status=200)
        
        return Response(serializer.errors, status=400)
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)



@api_view(['POST'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])  
def create_ground_level_manager(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    serializer = Add_GLM_Serializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def list_ground_level_managers(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    managers = Ground_level_managers_reg.objects.all()
    serializer = Add_GLM_Serializer(managers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def retrieve_ground_level_manager(request, id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        manager = Ground_level_managers_reg.objects.get(id=id)
    except Ground_level_managers_reg.DoesNotExist:
        return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = Add_GLM_Serializer(manager)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def update_ground_level_manager(request, id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        manager = Ground_level_managers_reg.objects.get(pk=id)
    except Ground_level_managers_reg.DoesNotExist:
        return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = Add_GLM_Serializer(manager, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def delete_ground_level_manager(request, id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        manager = Ground_level_managers_reg.objects.get(id=id)
    except Ground_level_managers_reg.DoesNotExist:
        return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)

    manager.delete()
    
    return Response({"message": "Manager deleted successfully"}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def list_employees(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    sales_managers = Sales_manager_reg.objects.all()
    list_salesmanagers = AddSalesManagerSerializer(sales_managers,many=True).data
    glm_staff = Ground_level_managers_reg.objects.all()
    list_glm = Add_GLM_Serializer(glm_staff,many=True).data
    employee_list = {
        "Salesmanager_Employees":{
            "SalesManagers":list_salesmanagers,
        },
        "GLM_Employees":{
            "GLM_staff":list_glm
        }
    }
    return Response(employee_list,status=status.HTTP_200_OK)





@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def salesmanager_details(request):
    staff = request.user

    # Ensure the authenticated user is a Sales Manager
    if not hasattr(staff, 'sales_manager_reg'):
        return Response({"error": "Not a valid sales manager"}, status=403)
    
    salesmanager = Sales_manager_reg.objects.get(user=staff.id)
    serializer = Add_GLM_Serializer(salesmanager).data
    return Response(serializer,status=status.HTTP_200_OK)



    
@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def list_of_salesmangers(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    salesmanager= Sales_manager_reg.objects.all()
    serializer =GetSalesManagerSerializer(salesmanager,many=True).data 
    return Response(serializer,status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def Single_salesmanger(request,salesmanager_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    salesmanager= Sales_manager_reg.objects.filter(id=salesmanager_id)
    serializer =GetSalesManagerSerializer(salesmanager,many=True).data 
    return Response(serializer,status=status.HTTP_200_OK)




