from django.urls import path

from . import views

app_name = "reporting"

urlpatterns = [
    path("", views.ReportingDashboardView.as_view(), name="index"),
    path("annual-zakat/", views.AnnualZakatReportView.as_view(), name="annual_zakat"),
    path("fee-collection/", views.FeeCollectionReportView.as_view(), name="fee_collection"),
    path("export/members/", views.MembersExportView.as_view(), name="export_members"),
    path("export/donations/", views.DonationsExportView.as_view(), name="export_donations"),
    path("export/income/", views.IncomeExportView.as_view(), name="export_income"),
    path("export/expenses/", views.ExpenseExportView.as_view(), name="export_expenses"),
    path("export/transfers/", views.TransfersExportView.as_view(), name="export_transfers"),
    path("export/students/", views.StudentsExportView.as_view(), name="export_students"),
    path("export/payments/", views.PaymentsExportView.as_view(), name="export_payments"),
    path("export/events/", views.EventsExportView.as_view(), name="export_events"),
    path("export/items/", views.ItemsExportView.as_view(), name="export_items"),
    path("export/movements/", views.MovementsExportView.as_view(), name="export_movements"),
    path("export/annual-zakat/", views.AnnualZakatCSVExportView.as_view(), name="export_annual_zakat"),
    path("export/fee-collection/", views.FeeCollectionCSVExportView.as_view(), name="export_fee_collection"),
]
