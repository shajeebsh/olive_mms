from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.FinanceDashboardView.as_view(), name="index"),
    path("funds/", views.FundListView.as_view(), name="funds"),
    path("funds/new/", views.FundCreateView.as_view(), name="fund_create"),
    path("funds/<int:pk>/edit/", views.FundUpdateView.as_view(), name="fund_update"),
    path("expenses/", views.ExpenseListView.as_view(), name="expenses"),
    path("expenses/new/", views.ExpenseCreateView.as_view(), name="expense_create"),
    path("expenses/<int:pk>/edit/", views.ExpenseUpdateView.as_view(), name="expense_update"),
    path("expenses/<int:pk>/approve/", views.ExpenseApproveView.as_view(), name="expense_approve"),
    path("income/", views.IncomeListView.as_view(), name="income"),
    path("income/new/", views.IncomeCreateView.as_view(), name="income_create"),
    path("transfers/", views.FundTransferListView.as_view(), name="transfers"),
    path("transfers/new/", views.FundTransferCreateView.as_view(), name="transfer_create"),
]
