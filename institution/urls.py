from django.urls import path

from . import views

app_name = "institution"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("setup/", views.SetupView.as_view(), name="setup"),
    path("edit/", views.ProfileEditView.as_view(), name="edit"),
]
