from django.urls import path

from . import views

app_name = "members"

urlpatterns = [
    path("", views.MemberListView.as_view(), name="index"),
    path("members/new/", views.MemberCreateView.as_view(), name="member_create"),
    path("members/<int:pk>/", views.MemberDetailView.as_view(), name="member_detail"),
    path("members/<int:pk>/edit/", views.MemberUpdateView.as_view(), name="member_update"),
    path("members/<int:pk>/delete/", views.MemberDeleteView.as_view(), name="member_delete"),
    path("families/", views.FamilyListView.as_view(), name="family_list"),
    path("families/new/", views.FamilyCreateView.as_view(), name="family_create"),
    path("families/<int:pk>/", views.FamilyDetailView.as_view(), name="family_detail"),
    path("families/<int:pk>/edit/", views.FamilyUpdateView.as_view(), name="family_update"),
    path("families/<int:pk>/delete/", views.FamilyDeleteView.as_view(), name="family_delete"),
]
