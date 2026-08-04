from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from donations.models import Donation, DonationType
from finance.models import Fund
from madrassa.models import Fee, FeePayment, Student


class ReportingViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="reporter@example.com", password="testpass", full_name="Reporter"
        )
        self.fund = Fund.objects.create(name="General Fund", code="GEN")
        self.donation_type = DonationType.objects.create(code="ZAKAT", name="Zakat")
        self.zakat = Donation.objects.create(
            donation_type=self.donation_type,
            fund=self.fund,
            amount=Decimal("500.00"),
            date=date.today(),
        )
        Donation.objects.create(
            donation_type=DonationType.objects.create(code="GENERAL", name="General"),
            fund=self.fund,
            amount=Decimal("250.00"),
            date=date.today(),
        )
        self.student = Student.objects.create(full_name="Student One")
        self.fee = Fee.objects.create(name="Monthly", amount=Decimal("100.00"))
        FeePayment.objects.create(
            student=self.student,
            fee=self.fee,
            amount=Decimal("100.00"),
            date=date.today(),
        )

    def test_reports_require_login(self):
        for url in [
            reverse("reporting:index"),
            reverse("reporting:annual_zakat"),
            reverse("reporting:fee_collection"),
            reverse("reporting:export_members"),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)

    def test_dashboard_renders_kpis(self):
        self.client.login(email="reporter@example.com", password="testpass")
        response = self.client.get(reverse("reporting:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["year_donations"], Decimal("750.00"))
        self.assertContains(response, "750.00")

    def test_annual_zakat_report(self):
        self.client.login(email="reporter@example.com", password="testpass")
        response = self.client.get(reverse("reporting:annual_zakat"))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx["zakat_total"], Decimal("500.00"))
        self.assertEqual(ctx["grand_total"], Decimal("750.00"))
        self.assertIn(b"750.00", response.content)

    def test_fee_collection_report(self):
        self.client.login(email="reporter@example.com", password="testpass")
        response = self.client.get(reverse("reporting:fee_collection"))
        self.assertEqual(response.status_code, 200)
        ctx = response.context
        self.assertEqual(ctx["collected_total"], Decimal("100.00"))
        self.assertTrue(ctx["has_payments"])

    def test_csv_exports(self):
        self.client.login(email="reporter@example.com", password="testpass")
        for url_name in [
            "export_members",
            "export_donations",
            "export_income",
            "export_expenses",
            "export_transfers",
            "export_students",
            "export_payments",
            "export_events",
            "export_items",
            "export_movements",
            "export_annual_zakat",
            "export_fee_collection",
        ]:
            response = self.client.get(reverse("reporting:" + url_name))
            self.assertEqual(response.status_code, 200, url_name)
            self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8", url_name)

    def test_donation_export_honors_filters(self):
        self.client.login(email="reporter@example.com", password="testpass")
        url = reverse("reporting:export_donations") + f"?donation_type={self.donation_type.pk}"
        response = self.client.get(url)
        self.assertContains(response, "RCP-")
        self.assertNotContains(response, "250.00")
