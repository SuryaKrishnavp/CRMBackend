from django.shortcuts import render
from rest_framework.decorators import api_view,permission_classes
from auth_section.permissions import IsCustomAdminUser,IsSalesManagerUser
from rest_framework.response import Response
from .serializers import ProjectSerializer,DataBankProjectSerializer,ProjectCreateSerializer,AddDataBankSerializer,RemoveDataBankSerializer,ProjectEditSerializer
from rest_framework import status
from databank_section.models import DataBank
from .models import Project_db
from rest_framework.permissions import AllowAny,IsAuthenticated
from leads_section.models import Leads
from auth_section.models import Sales_manager_reg
from databank_section.serializers import DataBankGETSerializer
# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def create_project(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    serializer = ProjectCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        # Save the project
        project = serializer.save()
        
        return Response({
            'message': "Project created successfully",
            'project_id': project.id
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def add_data_banks_to_project(request, project_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        project = Project_db.objects.get(id=project_id)
    except Project_db.DoesNotExist:
        return Response({'message': "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    # Pass request data to serializer for validation
    serializer = AddDataBankSerializer(data=request.data)

    if serializer.is_valid():
        data_bank_ids = serializer.validated_data['data_bank_ids']

        # Fetch DataBanks to be added
        data_banks_to_add = DataBank.objects.filter(id__in=data_bank_ids)

        if not data_banks_to_add.exists():
            return Response({'message': "No matching DataBank records found"}, status=status.HTTP_400_BAD_REQUEST)

        # Add DataBanks to the current project
        project.data_bank.add(*data_banks_to_add)

        return Response({
            'message': f'DataBanks {data_bank_ids} added successfully to project {project.project_name}'
        }, status=status.HTTP_200_OK)

    # Return validation errors if any
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def edit_project(request, project_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        project = Project_db.objects.get(id=project_id)
    except Project_db.DoesNotExist:
        return Response({'message': "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    # Pass project instance and request data to serializer
    serializer = ProjectEditSerializer(project, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': "Project updated successfully",
            'updated_data': serializer.data
        }, status=status.HTTP_200_OK)

    # Return validation errors if any
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def remove_data_banks(request, project_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        project = Project_db.objects.get(id=project_id)
    except Project_db.DoesNotExist:
        return Response({'message': "Project not found"}, status=status.HTTP_404_NOT_FOUND)

    # Validate request data using serializer
    serializer = RemoveDataBankSerializer(data=request.data)

    if serializer.is_valid():
        data_bank_ids = serializer.validated_data['data_bank_ids']

        # Filter DataBanks that are linked to this project
        data_banks_to_remove = project.data_bank.filter(id__in=data_bank_ids)

        if not data_banks_to_remove.exists():
            return Response({
                'message': "No matching DataBanks found in this project."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Remove DataBanks from the project
        project.data_bank.remove(*data_banks_to_remove)

        return Response({
            'message': f'DataBanks {data_bank_ids} removed successfully from project {project.project_name}'
        }, status=status.HTTP_200_OK)

    # Return validation errors if any
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   


    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def list_projects(request):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    projects = Project_db.objects.prefetch_related('data_bank').all()
    project_data = []

    for project in projects:
        # ✅ Get all databank IDs linked to the project
        databank_ids = project.data_bank.values_list('id', flat=True)

        # ✅ Get all leads from the databank entries linked to this project
        databank_leads = Leads.objects.filter(databank_lead__id__in=databank_ids)

        # ✅ Get the total number of leads in the project
        total_databank_count = databank_leads.count()

        # ✅ Get the number of closed leads in the project
        closed_leads_count = databank_leads.filter(
            stage__in=["Closed Successfully", "Closed by Someone", "Droped Lead"]
        ).count()

        # ✅ Calculate progress percentage
        progress_percentage = (
            (closed_leads_count / total_databank_count) * 100
            if total_databank_count > 0
            else 0
        )

        # ✅ Serialize the project and include progress
        project_serializer = ProjectSerializer(project).data

        # ✅ Add progress data to project details
        project_serializer.update({
            "total_databank_count": total_databank_count,
            "closed_leads_count": closed_leads_count,
            "progress_percentage": round(progress_percentage, 2),
        })

        project_data.append(project_serializer)

    return Response({
        'message': "List of all projects",
        'projects': project_data
    }, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def remove_project(request,project_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    project = Project_db.objects.get(id=project_id)
    project_name = project.project_name
    project.delete()
    return Response({"message":f"{project_name} is successfully removed"})


@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def get_project_progress(request, project_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        # ✅ Get the project
        project = Project_db.objects.get(id=project_id)

        # ✅ Get all related databank collections in the project
        databank_ids = project.data_bank.values_list('id', flat=True)
        databank_leads = Leads.objects.filter(id__in=DataBank.objects.filter(id__in=databank_ids).values_list('lead_id', flat=True))

        # ✅ Get the total number of databank leads in the project
        total_databank_count = databank_leads.count()

        # ✅ Get the number of closed leads in the databank
        closed_leads_count = databank_leads.filter(
            stage__in=["Closed Successfully", "Closed by Someone", "Droped Lead"]
        ).count()

        # ✅ Calculate progress percentage
        progress_percentage = (
            (closed_leads_count / total_databank_count) * 100
            if total_databank_count > 0
            else 0
        )

        # ✅ Prepare response data
        response_data = {
            "project_id": project.id,
            "project_name": project.project_name,
            "total_databank_count": total_databank_count,
            "closed_leads_count": closed_leads_count,
            "progress_percentage": round(progress_percentage, 2),
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Project_db.DoesNotExist:
        return Response({"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND)
    
    
    
@api_view(['GET'])
@permission_classes([IsAuthenticated,IsSalesManagerUser])
def salesmanager_included_project(request):
    staff = request.user

    # Ensure staff exists
    sales_staff = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not sales_staff:
        return Response({'error': 'Invalid sales manager '}, status=status.HTTP_400_BAD_REQUEST)
    
    followed_projects = []

    # ✅ Get all projects
    projects = Project_db.objects.all()
    
    for project in projects:
        # ✅ Get all databank entries followed by this staff (sales manager)
        databank_entries = project.data_bank.filter(follower_id=sales_staff)

        if databank_entries.exists():
            # ✅ Get all databank IDs followed by the staff
            databank_ids = databank_entries.values_list('id', flat=True)

            # ✅ Get all related leads for these databank entries
            databank_leads = Leads.objects.filter(databank_lead__id__in=databank_ids)

            # ✅ Count total leads in this project for the sales manager
            total_databank_count = databank_leads.count()

            # ✅ Count closed leads in this project for the sales manager
            closed_leads_count = databank_leads.filter(
                stage__in=["Closed Successfully", "Closed by Someone", "Droped Lead"]
            ).count()

            # ✅ Calculate progress percentage
            progress_percentage = (
                (closed_leads_count / total_databank_count) * 100
                if total_databank_count > 0
                else 0
            )

            # ✅ Add project details along with progress
            followed_projects.append({
                "project_id": project.id,
                "project_icon": project.project_icon.url if project.project_icon else None,
                "project_name": project.project_name,
                "priority":project.importance,
                "started_date":project.start_date,
                "dead_line":project.deadline,
                "total_databank_count": total_databank_count,
                "closed_leads_count": closed_leads_count,
                "progress_percentage": round(progress_percentage, 2),
            })

    if not followed_projects:
        return Response({'message': "No projects found for this sales manager."}, status=404)

    return Response(followed_projects, status=200)




@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def salesmanager_project_admin(request, staff_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    
    followed_projects = []

    # ✅ Get all projects followed by the sales manager
    projects = Project_db.objects.all()
    for project in projects:
        # ✅ Check if the sales manager is following databank entries in the project
        databank_entries = project.data_bank.filter(follower_id=staff_id)

        if databank_entries.exists():
            # ✅ Calculate project progress for the project
            databank_ids = project.data_bank.values_list('id', flat=True)
            databank_leads = Leads.objects.filter(id__in=DataBank.objects.filter(id__in=databank_ids).values_list('lead_id', flat=True))


            # ✅ Get the total number of databank leads in the project
            total_databank_count = databank_leads.count()

            # ✅ Get the number of closed leads in the databank
            closed_leads_count = databank_leads.filter(
                stage__in=["Closed Successfully", "Closed by Someone", "Droped Lead"]
            ).count()

            # ✅ Calculate progress percentage
            progress_percentage = (
                (closed_leads_count / total_databank_count) * 100
                if total_databank_count > 0
                else 0
            )

            followed_projects.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "total_databank_count": total_databank_count,
                "closed_leads_count": closed_leads_count,
                "progress_percentage": round(progress_percentage, 2),
            })

    if not followed_projects:
        return Response({'message': "No projects found for this sales manager."}, status=404)

    return Response(followed_projects, status=200)
    
    




@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSalesManagerUser])
def get_single_project_salesmanger(request, project_id):
    staff = request.user

    # ✅ Ensure staff exists
    sales_staff = Sales_manager_reg.objects.filter(user=staff.id).first()
    if not sales_staff:
        return Response({"error": "Invalid sales manager"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # ✅ Get the project
        project = Project_db.objects.prefetch_related("data_bank").get(id=project_id)

        # ✅ Get databanks followed by this sales manager for the project
        databank_entries = project.data_bank.filter(follower_id=sales_staff)

        # ✅ Get all databank IDs followed by the sales manager
        databank_ids = databank_entries.values_list("id", flat=True)

        # ✅ Get all related leads for these databank entries
        databank_leads = Leads.objects.filter(databank_lead__id__in=databank_ids)

        # ✅ Count total leads in this project for the sales manager
        total_databank_count = databank_leads.count()

        # ✅ Count closed leads in this project
        closed_leads_count = databank_leads.filter(
            stage__in=["Closed Successfully", "Closed by Someone", "Droped Lead"]
        ).count()

        # ✅ Calculate progress percentage
        progress_percentage = (
            (closed_leads_count / total_databank_count) * 100
            if total_databank_count > 0
            else 0
        )

        # ✅ Serialize databanks
        databanks_data = DataBankGETSerializer(databank_entries, many=True).data

        # ✅ Prepare project details with databanks
        project_data = {
            "id": project.id,
            "data_bank": databanks_data,  # ✅ Include databank details
            "project_icon": project.project_icon.url if project.project_icon else None,
            "project_name": project.project_name,
            "importance": project.importance,
            "start_date": project.start_date,
            "time_stamp": project.time_stamp,
            "deadline": project.deadline,
            "description": project.description,
            "total_databank_count": total_databank_count,
            "closed_leads_count": closed_leads_count,
            "progress_percentage": round(progress_percentage, 2),
        }

        return Response(project_data, status=200)

    except Project_db.DoesNotExist:
        return Response({"message": "Project not found."}, status=404)



@api_view(['GET'])
@permission_classes([IsAuthenticated,IsCustomAdminUser])
def retrive_project(request, project_id):
    admin = request.user  # `request.user` will be automatically populated with the authenticated user

    # Check if the user is an admin
    if not hasattr(admin, 'admin_reg'):
        return Response({'error': 'Admin authentication required'}, status=status.HTTP_403_FORBIDDEN)
    try:
        # ✅ Get the project
        project = Project_db.objects.prefetch_related("data_bank").get(id=project_id)

        # ✅ Get databanks followed by this sales manager for the project
        databank_entries = project.data_bank.all()

        # ✅ Get all databank IDs followed by the sales manager
        databank_ids = databank_entries.values_list("id", flat=True)

        # ✅ Get all related leads for these databank entries
        databank_leads = Leads.objects.filter(databank_lead__id__in=databank_ids)

        # ✅ Count total leads in this project for the sales manager
        total_databank_count = databank_leads.count()

        # ✅ Count closed leads in this project
        closed_leads_count = databank_leads.filter(
            stage__in=["Closed Successfully", "Closed by Someone", "Droped Lead"]
        ).count()

        # ✅ Calculate progress percentage
        progress_percentage = (
            (closed_leads_count / total_databank_count) * 100
            if total_databank_count > 0
            else 0
        )

        # ✅ Serialize databanks
        databanks_data = DataBankGETSerializer(databank_entries, many=True).data

        # ✅ Prepare project details with databanks
        project_data = {
            "id": project.id,
            "data_bank": databanks_data,  # ✅ Include databank details
            "project_icon": project.project_icon.url if project.project_icon else None,
            "project_name": project.project_name,
            "importance": project.importance,
            "start_date": project.start_date,
            "time_stamp": project.time_stamp,
            "deadline": project.deadline,
            "description": project.description,
            "total_databank_count": total_databank_count,
            "closed_leads_count": closed_leads_count,
            "progress_percentage": round(progress_percentage, 2),
        }

        return Response(project_data, status=200)

    except Project_db.DoesNotExist:
        return Response({"message": "Project not found."}, status=404)