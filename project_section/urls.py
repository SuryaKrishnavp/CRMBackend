from django.urls import path
from .views import (create_project,edit_project,retrive_project,list_projects,
                    add_data_banks_to_project,remove_data_banks,remove_project,
                    get_project_progress,salesmanager_included_project,salesmanager_project_admin,
                    get_single_project_salesmanger)

urlpatterns = [
    path("create_project/", create_project, name="create_project"),
    path('edit_project/<int:project_id>/',edit_project,name="edit_project"),
    path('retrive_project/<int:project_id>/',retrive_project,name="retrive_project"),
    path('list_projects/',list_projects,name="list_projects"),
    path('add_data_into_project/<int:project_id>/',add_data_banks_to_project,name="add_data"),
    path('remove_data_banks/<int:project_id>/',remove_data_banks,name="remove_db"),
    path('remove_project/<int:project_id>/',remove_project,name="remove_project"),
    path('get_project_progress/<int:project_id>/',get_project_progress,name="project_progress"),
    path('sales_manager_projects/',salesmanager_included_project,name="salesmanger_projects"),
    path('salesmanager_project_admin/<int:staff_id>/',salesmanager_project_admin,name="salesmanger_project_admin"),
    path('salesmanger_single_project/<int:project_id>/',get_single_project_salesmanger,name="single_project_salesmanger")
]
