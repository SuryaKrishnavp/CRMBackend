from django.urls import path
from .views import (Login_func,Add_Salesman,forgot_password,reset_password,SalesManager_details,
    delete_sales_manager,
    update_admin,
    create_ground_level_manager,
    list_ground_level_managers,
    retrieve_ground_level_manager,
    update_ground_level_manager,
    delete_ground_level_manager,
    Update_Salesman,list_employees,get_admin,salesmanager_details,create_admin,
    list_of_salesmangers,update_sales_manager_password,Single_salesmanger)



urlpatterns = [
    path('addadmin/',create_admin,name="createadmin"),
    path('login/', Login_func ,name="login"),
    path('forgot-password/',forgot_password,name="forgotpass"),
    path('logic/reset-password/<str:token>/',reset_password,name="resetpasswordlogic"),
    path('add_salesmanager/',Add_Salesman ,name="addsalesmanager"),
    path('update_salesmanager/<int:salesmanager_id>/', Update_Salesman, name='update_salesman'),
    path('view-salesmanager/',SalesManager_details,name="salesmanager-details"),
    path('delete_salesmanager/<int:sales_manager_id>/',delete_sales_manager,name="delete-salesmanager"),
    path('update-admin/',update_admin,name="update-admin"),
    path('add_glm/',create_ground_level_manager,name="add_glm"),
    path('list_glm/',list_ground_level_managers,name="list_glm"),
    path('retrive_glm/<int:id>/',retrieve_ground_level_manager,name="retrive_glm"),
    path('update_glm/<int:id>/',update_ground_level_manager,name="update_glm"),
    path('delete_glm/<int:id>/',delete_ground_level_manager,name="delete_glm"),
    path('list_employees/',list_employees,name="list_employees"),
    path('get_admin/',get_admin,name="get_admin"),
    path('salesmanager_details/',salesmanager_details,name="salesmanager_details"),
    path('list_of_salesmangers/',list_of_salesmangers,name="list_of_salesmanger"),
    path('update_salesmanager_password/<int:salesmanager_id>/',update_sales_manager_password,name="update_salesmanager_password"),
    path('single_salesmanager/<int:salesmanager_id>/',Single_salesmanger,name="single_salesmanager")
]