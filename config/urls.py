"""URL configuration for config project."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("core.urls")),
    path("institution/", include("institution.urls")),
    path("members/", include("members.urls")),
    path("donations/", include("donations.urls")),
    path("finance/", include("finance.urls")),
    path("madrassa/", include("madrassa.urls")),
]
