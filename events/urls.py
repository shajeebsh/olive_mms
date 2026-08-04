from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="index"),
    path("new/", views.EventCreateView.as_view(), name="event_create"),
    path("<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("<int:pk>/edit/", views.EventUpdateView.as_view(), name="event_update"),
    path("<int:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),
    path("attendances/new/", views.EventAttendanceCreateView.as_view(), name="attendance_create"),
    path("attendances/<int:pk>/delete/", views.EventAttendanceDeleteView.as_view(), name="attendance_delete"),
    path("volunteers/", views.VolunteerListView.as_view(), name="volunteers"),
]
