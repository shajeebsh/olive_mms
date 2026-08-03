from django.urls import path

from . import views

app_name = "donations"

urlpatterns = [
    path("", views.DonationListView.as_view(), name="index"),
    path("donations/new/", views.DonationCreateView.as_view(), name="donation_create"),
    path("donations/<int:pk>/", views.DonationDetailView.as_view(), name="donation_detail"),
    path("donations/<int:pk>/receipt/", views.DonationReceiptView.as_view(), name="donation_receipt"),
    path("donations/<int:pk>/edit/", views.DonationUpdateView.as_view(), name="donation_update"),
    path("donations/<int:pk>/delete/", views.DonationDeleteView.as_view(), name="donation_delete"),
    path("pledges/", views.PledgeListView.as_view(), name="pledges"),
    path("pledges/new/", views.PledgeCreateView.as_view(), name="pledge_create"),
    path("types/", views.DonationTypeListView.as_view(), name="types"),
    path("types/new/", views.DonationTypeCreateView.as_view(), name="type_create"),
]
