from django.urls import path
from .views import (create_followup,list_followups,edit_followup,
                    cancel_followup,get_followup_reminders,salesmanager_today_upcoming_events,
                    salesmanager_all_events,leadwise_followups,followup_status_entry)
urlpatterns = [
    path('createfollowup/<int:lead_id>/',create_followup,name="create_followup"),
    path('list_followups/',list_followups,name="listfollowups"),
    path('edit_followup/<int:followup_id>/', edit_followup, name='edit_followup'),
    path('cancel_followup/<int:followup_id>/', cancel_followup, name='cancel_followup'),
    path("followup-reminders/", get_followup_reminders, name="followup_reminders"),
    path('Upcomming_salesmanager_event/',salesmanager_today_upcoming_events,name="upcomming_events"),
    path('salesmanager_all_events/',salesmanager_all_events,name="salesmanager_all_events"),
    path('lead_wise_followup/<int:lead_id>/',leadwise_followups,name='leadwisefollowups'),
    path('followup_status_entry/<int:followup_id>/',followup_status_entry,name="followup_status")

]
