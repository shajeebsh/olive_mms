from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.ItemListView.as_view(), name="index"),
    path("items/new/", views.ItemCreateView.as_view(), name="item_create"),
    path("items/<int:pk>/edit/", views.ItemUpdateView.as_view(), name="item_update"),
    path("items/<int:pk>/delete/", views.ItemDeleteView.as_view(), name="item_delete"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    path("movements/", views.StockMovementListView.as_view(), name="movements"),
    path("movements/new/", views.StockMovementCreateView.as_view(), name="movement_create"),
    path("movements/<int:pk>/delete/", views.StockMovementDeleteView.as_view(), name="movement_delete"),
    path("distributions/", views.DistributionListView.as_view(), name="distributions"),
    path("distributions/new/", views.DistributionCreateView.as_view(), name="distribution_create"),
]
