"""Reporting: cross-module dashboard, annual/zakat report, fee collection report,
and CSV exports for the main module lists.
"""

import csv
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView

from core.utils import money
from donations.models import Donation, DonationType
from events.models import Event
from finance.models import Expense, Fund, FundTransfer, Income
from inventory.models import Item, StockLevel, StockMovement
from madrassa.models import Class, Enrollment, Fee, FeePayment, Student
from members.models import Member

ZAKAT_CODES = ["ZAKAT", "FITRA"]


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


class ReportingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = date.today()

        ctx["member_count"] = Member.objects.count()
        ctx["active_members"] = Member.objects.filter(membership_status=Member.MembershipStatus.ACTIVE).count()
        ctx["current_year"] = today.year
        ctx["donation_count"] = Donation.objects.filter(date__year=today.year).count()
        ctx["year_donations"] = money(
            Donation.objects.filter(date__year=today.year).aggregate(s=Sum("amount"))["s"]
        )
        funds = Fund.objects.all()
        ctx["total_balance"] = money(sum(f.balance for f in funds))
        ctx["fund_count"] = funds.count()
        ctx["active_students"] = Student.objects.filter(status=Student.Status.ACTIVE).count()
        ctx["upcoming_events"] = Event.objects.filter(date_from__gte=today).exclude(
            status=Event.Status.CANCELLED
        ).count()
        ctx["low_stock_items"] = sum(
            1 for item in Item.objects.select_related("stock_level") if item.is_low_stock
        )

        ctx["month_income"] = money(
            Income.objects.filter(date__year=today.year, date__month=today.month).aggregate(
                s=Sum("amount")
            )["s"]
        )
        ctx["month_expense"] = money(
            Expense.objects.filter(date__year=today.year, date__month=today.month).aggregate(
                s=Sum("amount")
            )["s"]
        )

        ctx["donation_type_labels"], ctx["donation_type_values"] = self.donation_type_breakdown(today.year)
        ctx["monthly_labels"], ctx["monthly_income"], ctx["monthly_expense"] = self.monthly_trend()

        ctx["recent_donations"] = Donation.objects.select_related("donation_type", "fund").order_by(
            "-date", "-id"
        )[:6]
        ctx["recent_payments"] = FeePayment.objects.select_related("student", "fee").order_by(
            "-date", "-id"
        )[:6]
        ctx["recent_expenses"] = Expense.objects.select_related("fund").order_by("-date", "-id")[:6]
        ctx["recent_distributions"] = StockMovement.objects.filter(
            movement_type=StockMovement.MovementType.OUT
        ).select_related("item")[:6]
        return ctx

    def donation_type_breakdown(self, year):
        rows = (
            Donation.objects.filter(date__year=year)
            .values("donation_type__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        labels = [row["donation_type__name"] for row in rows]
        values = [float(money(row["total"])) for row in rows]
        return labels, values

    def monthly_trend(self):
        today = date.today()
        first = (today.replace(day=28) - timedelta(days=30 * 5)).replace(day=1)

        def by_month(model):
            return {
                row["month"].strftime("%Y-%m"): money(row["total"])
                for row in model.objects.filter(date__gte=first)
                .annotate(month=TruncMonth("date"))
                .values("month")
                .annotate(total=Sum("amount"))
            }

        income_rows = by_month(Income)
        expense_rows = by_month(Expense)

        labels, income, expense = [], [], []
        year, month = first.year, first.month
        for _ in range(6):
            key = f"{year:04d}-{month:02d}"
            labels.append(date(year, month, 1).strftime("%b"))
            income.append(float(income_rows.get(key, 0)))
            expense.append(float(expense_rows.get(key, 0)))
            month += 1
            if month > 12:
                month = 1
                year += 1
        return labels, income, expense


class AnnualZakatReportView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/annual_zakat.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year = int(self.request.GET.get("year", "") or date.today().year)
        ctx["year"] = year
        ctx["years"] = sorted({d.year for d in Donation.objects.dates("date", "year")})
        if not ctx["years"]:
            ctx["years"] = [date.today().year]

        donations = Donation.objects.filter(date__year=year)
        ctx["grand_total"] = money(donations.aggregate(s=Sum("amount"))["s"])
        ctx["donation_count"] = donations.count()
        ctx["zakat_total"] = money(
            donations.filter(donation_type__code__in=ZAKAT_CODES).aggregate(s=Sum("amount"))["s"]
        )
        ctx["zakat_pct"] = (
            ctx["zakat_total"] / ctx["grand_total"] * 100 if ctx["grand_total"] else 0
        )
        ctx["zakat_codes"] = ZAKAT_CODES
        ctx["has_donations"] = donations.exists()

        ctx["type_totals"] = (
            donations.values("donation_type__name", "donation_type__code")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")
        )

        monthly = {
            row["month"].month: money(row["total"])
            for row in donations.annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("amount"))
        }
        ctx["monthly_labels"] = []
        ctx["monthly_values"] = []
        for m in range(1, 13):
            ctx["monthly_labels"].append(date(year, m, 1).strftime("%b"))
            ctx["monthly_values"].append(float(monthly.get(m, 0)))
        return ctx


class FeeCollectionReportView(LoginRequiredMixin, TemplateView):
    template_name = "reporting/fee_collection.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        year = int(self.request.GET.get("year", "") or date.today().year)
        class_id = self.request.GET.get("class", "").strip()
        ctx["year"] = year
        ctx["years"] = sorted({d.year for d in FeePayment.objects.dates("date", "year")})
        if not ctx["years"]:
            ctx["years"] = [date.today().year]
        ctx["classes"] = Class.objects.filter(is_active=True)
        ctx["selected_class"] = class_id

        payments = FeePayment.objects.filter(date__year=year).select_related("student", "fee")
        if class_id:
            payments = payments.filter(student__enrollments__madrassa_class_id=class_id).distinct()

        ctx["collected_total"] = money(payments.aggregate(s=Sum("amount"))["s"])
        ctx["payment_count"] = payments.count()
        ctx["has_payments"] = payments.exists()

        monthly = {
            row["month"].month: money(row["total"])
            for row in payments.annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(total=Sum("amount"))
        }
        ctx["monthly_labels"] = []
        ctx["monthly_values"] = []
        for m in range(1, 13):
            ctx["monthly_labels"].append(date(year, m, 1).strftime("%b"))
            ctx["monthly_values"].append(float(monthly.get(m, 0)))

        class_totals = {}
        for payment in payments:
            key = payment.student.enrollments.filter(
                academic_year=str(year)
            ).first() or payment.student.enrollments.order_by("-academic_year").first()
            class_totals.setdefault(key.madrassa_class_id if key else None, []).append(payment.amount)
        ctx["class_summary"] = self.build_class_summary(class_totals, year)
        summary = [row for row in ctx["class_summary"] if row["expected"] and row["collected"]]
        ctx["overall_rate"] = (
            round(100 * sum(row["collected"] for row in summary) / sum(row["expected"] for row in summary), 1)
            if summary and sum(row["expected"] for row in summary)
            else None
        )

        ctx["student_totals"] = (
            payments.values("student__full_name")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")[:10]
        )
        return ctx

    def build_class_summary(self, class_totals, year):
        rows = []
        classes = Class.objects.prefetch_related("fees", "enrollments")
        for cls in classes:
            amounts = class_totals.get(cls.pk, [])
            enrolled = cls.enrollments.filter(
                academic_year=str(year), status=Enrollment.Status.ENROLLED
            ).count()
            fee_total = sum(f.amount for f in cls.fees.filter(is_active=True)) or None
            expected = fee_total * enrolled if fee_total is not None else None
            collected = sum(amounts)
            rate = None
            if expected and expected > 0:
                rate = round(100 * collected / expected, 1)
            rows.append(
                {
                    "class": cls,
                    "enrolled": enrolled,
                    "collected": money(collected),
                    "expected": money(expected) if expected is not None else None,
                    "rate": rate,
                }
            )
        return rows


class BaseCSVExportView(LoginRequiredMixin, View):
    filename = "export.csv"
    headers = []

    def get_rows(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        return csv_response(self.filename, self.headers, self.get_rows())


class MembersExportView(BaseCSVExportView):
    filename = "members.csv"
    headers = ["Name", "Family", "Phone", "Email", "Role", "Status", "Joined"]

    def get_rows(self):
        queryset = Member.objects.select_related("family")
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(full_name__icontains=q) | Q(family__name__icontains=q))
        return [
            [
                m.full_name,
                m.family.name if m.family_id else "",
                m.phone,
                m.email,
                m.get_member_role_display(),
                m.get_membership_status_display(),
                m.join_date,
            ]
            for m in queryset.order_by("full_name")
        ]


class DonationsExportView(BaseCSVExportView):
    filename = "donations.csv"
    headers = ["Receipt", "Date", "Member", "Type", "Fund", "Amount", "Method", "Reference"]

    def get_rows(self):
        queryset = Donation.objects.select_related("donation_type", "fund", "member")
        donation_type = self.request.GET.get("donation_type", "").strip()
        method = self.request.GET.get("payment_method", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if donation_type:
            queryset = queryset.filter(donation_type_id=donation_type)
        if method:
            queryset = queryset.filter(payment_method=method)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return [
            [
                d.receipt_number,
                d.date,
                d.member.full_name if d.member_id else "",
                d.donation_type.name,
                d.fund.name,
                d.amount,
                d.get_payment_method_display(),
                d.reference_no,
            ]
            for d in queryset.order_by("-date", "-id")
        ]


class IncomeExportView(BaseCSVExportView):
    filename = "income.csv"
    headers = ["Date", "Fund", "Source", "Amount", "Description"]

    def get_rows(self):
        queryset = Income.objects.select_related("fund")
        fund = self.request.GET.get("fund", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if fund:
            queryset = queryset.filter(fund_id=fund)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return [
            [i.date, i.fund.name, i.source, i.amount, i.description]
            for i in queryset.order_by("-date", "-id")
        ]


class ExpenseExportView(BaseCSVExportView):
    filename = "expenses.csv"
    headers = ["Date", "Fund", "Category", "Description", "Payee", "Status", "Amount"]

    def get_rows(self):
        queryset = Expense.objects.select_related("fund")
        fund = self.request.GET.get("fund", "").strip()
        status = self.request.GET.get("status", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if fund:
            queryset = queryset.filter(fund_id=fund)
        if status:
            queryset = queryset.filter(status=status)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return [
            [e.date, e.fund.name, e.category, e.description, e.payee, e.get_status_display(), e.amount]
            for e in queryset.order_by("-date", "-id")
        ]


class TransfersExportView(BaseCSVExportView):
    filename = "transfers.csv"
    headers = ["Date", "From", "To", "Amount", "Note"]

    def get_rows(self):
        queryset = FundTransfer.objects.select_related("from_fund", "to_fund")
        return [
            [t.date, t.from_fund.name, t.to_fund.name, t.amount, t.note]
            for t in queryset.order_by("-date", "-id")
        ]


class StudentsExportView(BaseCSVExportView):
    filename = "students.csv"
    headers = ["Name", "Guardian", "Guardian Phone", "Admission Date", "Status"]

    def get_rows(self):
        queryset = Student.objects.all()
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(full_name__icontains=q) | Q(guardian__icontains=q))
        return [
            [s.full_name, s.guardian, s.guardian_phone, s.admission_date, s.get_status_display()]
            for s in queryset.order_by("full_name")
        ]


class PaymentsExportView(BaseCSVExportView):
    filename = "fee-payments.csv"
    headers = ["Receipt", "Date", "Student", "Fee", "Method", "Amount"]

    def get_rows(self):
        queryset = FeePayment.objects.select_related("student", "fee")
        return [
            [p.receipt_number, p.date, p.student.full_name, p.fee.name if p.fee_id else "", p.get_method_display(), p.amount]
            for p in queryset.order_by("-date", "-id")
        ]


class EventsExportView(BaseCSVExportView):
    filename = "events.csv"
    headers = ["Name", "Type", "From", "To", "Location", "Status", "Budget", "Attendees"]

    def get_rows(self):
        queryset = Event.objects.annotate(attendee_count=Count("attendees"))
        return [
            [e.name, e.get_event_type_display(), e.date_from, e.date_to or "", e.location, e.get_status_display(), e.budget, e.attendee_count]
            for e in queryset.order_by("-date_from")
        ]


class ItemsExportView(BaseCSVExportView):
    filename = "items.csv"
    headers = ["Name", "Category", "Unit", "Price", "In Stock", "Low Stock Threshold"]

    def get_rows(self):
        queryset = Item.objects.select_related("category", "stock_level")
        return [
            [i.name, i.category.name if i.category_id else "", i.unit, i.price, i.quantity, i.low_stock_threshold]
            for i in queryset.order_by("name")
        ]


class MovementsExportView(BaseCSVExportView):
    filename = "movements.csv"
    headers = ["Date", "Item", "Type", "Qty", "Purpose", "Recipient", "Event"]

    def get_rows(self):
        queryset = StockMovement.objects.select_related("item", "event")
        movement_type = self.request.GET.get("movement_type", "").strip()
        item = self.request.GET.get("item", "").strip()
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        if item:
            queryset = queryset.filter(item_id=item)
        return [
            [
                m.date,
                m.item.name,
                m.get_movement_type_display(),
                m.qty_change,
                m.purpose,
                m.recipient_display,
                m.event.name if m.event_id else "",
            ]
            for m in queryset.order_by("-date", "-id")
        ]


class AnnualZakatCSVExportView(BaseCSVExportView):
    filename = "annual-zakat.csv"
    headers = ["Donation Type", "Count", "Total"]

    def get_rows(self):
        year = int(self.request.GET.get("year", "") or date.today().year)
        rows = (
            Donation.objects.filter(date__year=year)
            .values("donation_type__name")
            .annotate(count=Count("id"), total=Sum("amount"))
            .order_by("-total")
        )
        return [[row["donation_type__name"], row["count"], row["total"]] for row in rows]


class FeeCollectionCSVExportView(BaseCSVExportView):
    filename = "fee-collection.csv"
    headers = ["Date", "Receipt", "Student", "Fee", "Method", "Amount"]

    def get_rows(self):
        year = int(self.request.GET.get("year", "") or date.today().year)
        class_id = self.request.GET.get("class", "").strip()
        payments = FeePayment.objects.filter(date__year=year).select_related("student", "fee")
        if class_id:
            payments = payments.filter(student__enrollments__madrassa_class_id=class_id).distinct()
        return [
            [p.date, p.receipt_number, p.student.full_name, p.fee.name if p.fee_id else "", p.get_method_display(), p.amount]
            for p in payments.order_by("-date", "-id")
        ]
