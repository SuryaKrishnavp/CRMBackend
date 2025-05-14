from django.urls import path
from .views import (update_event, delete_event,create_event,list_upcomming_events,
                    salesmanager_create_event,salesmanager_delete_event,Salesmanager_update_event,
                    list_upcoming_salesmanager_events,SalesManager_WorkHistory,Personal_workhistory,
                    CRM_performance_graph,get_scheduled_works,get_admin_scheduled_works,sheduled_admin_events,
                    Admin_Salesmanager_workhistory,Todays_upcomming_events,get_event_reminder_admin,SM_Event_status_entry,
                    Admin_Event_status_entry)

urlpatterns = [
    path('create_event/',create_event,name="create_event"),
    path('event_update/<int:id>/', update_event, name='update_event'),
    path('event_delete/<int:id>/', delete_event, name='delete_event'),
    path('list_events/',list_upcomming_events,name="list_events"),
    path('salesmanager_eventcreate/', salesmanager_create_event, name='salesmanager_create_event'),
    path('salesmanager_event_update/<int:id>/', Salesmanager_update_event, name='salesmanager_update_event'),
    path('salesmanager_event_delete/<int:id>/', salesmanager_delete_event, name='salesmanager_delete_event'),
    path('salesmanager_events_upcoming/', list_upcoming_salesmanager_events, name='list_upcoming_salesmanager_events'),
    path('salesmanager_workhistory/<int:salesmanager_id>/', SalesManager_WorkHistory, name='salesmanager_workhistory'),
    path('salesmanager_personal_workhistory/',Personal_workhistory,name="personal_workhistory"),
    path('crm_performance_overview/', CRM_performance_graph, name='crm_performance_overview'),
    path("scheduled_works_day/", get_scheduled_works, name="scheduled_works_api"),
    path("admin_scheduled_works_day/", get_admin_scheduled_works, name="admin_scheduled_works_api"),
    path("admin_sheduled_events/",sheduled_admin_events,name="sheduled_admin_events"),
    path('admin_salesmanager_workhistory/<int:staff_id>/',Admin_Salesmanager_workhistory,name="salesmanager_work_history_admin"),
    path('todays_upcoming_events/',Todays_upcomming_events,name="todays_upcoming"),
    path('get_event_reminder/',get_event_reminder_admin,name="get_event_reminder"),
    path('sm_event_status_entry/<int:event_id>/',SM_Event_status_entry,name="sm_event_status_entry"),
    path('admin_event_status_entry/<int:event_id>/',Admin_Event_status_entry,name="admin_event_status")

]
