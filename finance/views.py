from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from core.mixins import HTMXModalFormMixin, HTMXPartialMixin
from core.utils import money

from .forms import ExpenseForm, FundForm, FundTransferForm, IncomeForm
from .models import Expense, Fund, FundTransfer, Income


class FinanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "finance/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        funds = Fund.objects.all()
        ctx["funds"] = funds
        ctx["total_balance"] = money(sum(f.balance for f in funds))
        ctx["fund_count"] = funds.count()

        today = date.today()
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
        ctx["pending_expenses"] = Expense.objects.filter(status=Expense.Status.PENDING).count()

        ctx["monthly_labels"], ctx["monthly_income"], ctx["monthly_expense"] = self.monthly_trend()
        return ctx

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


class FundListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Fund
    template_name = "finance/fund_list.html"
    partial_template = "finance/partials/fund_list_content.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_balance"] = money(sum(f.balance for f in self.object_list))
        ctx["fund_count"] = self.object_list.count()
        return ctx


class FundCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Fund
    form_class = FundForm
    template_name = "finance/fund_form.html"
    success_url = reverse_lazy("finance:funds")

    def get_modal_title(self):
        return "Add fund"


class FundUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Fund
    form_class = FundForm
    template_name = "finance/fund_form.html"
    success_url = reverse_lazy("finance:funds")

    def get_modal_title(self):
        return f"Edit {self.object.name}"


class ExpenseListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Expense
    template_name = "finance/expense_list.html"
    partial_template = "finance/partials/expense_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Expense.objects.select_related("fund").order_by("-date", "-id")
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
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["funds"] = Fund.objects.filter(is_active=True)
        ctx["selected_fund"] = self.request.GET.get("fund", "")
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["date_from"] = self.request.GET.get("date_from", "")
        ctx["date_to"] = self.request.GET.get("date_to", "")
        ctx["expense_total"] = money(self.object_list.aggregate(s=Sum("amount"))["s"])
        ctx["pending_count"] = Expense.objects.filter(status=Expense.Status.PENDING).count()
        ctx["approved_count"] = Expense.objects.filter(status=Expense.Status.APPROVED).count()
        return ctx


class ExpenseCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/expense_form.html"
    success_url = reverse_lazy("finance:expenses")

    def get_modal_title(self):
        return "Record expense"


class ExpenseUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/expense_form.html"
    success_url = reverse_lazy("finance:expenses")

    def get_modal_title(self):
        return f"Edit expense {self.object.date}"


class ExpenseApproveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        expense = Expense.objects.get(pk=kwargs["pk"])
        expense.status = Expense.Status.APPROVED
        expense.save(update_fields=["status", "updated_at"])
        return HttpResponse("", status=204, headers={"HX-Trigger": '"listChanged"'})


class IncomeListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Income
    template_name = "finance/income_list.html"
    partial_template = "finance/partials/income_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Income.objects.select_related("fund", "donation").order_by("-date", "-id")
        fund = self.request.GET.get("fund", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if fund:
            queryset = queryset.filter(fund_id=fund)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["funds"] = Fund.objects.filter(is_active=True)
        ctx["selected_fund"] = self.request.GET.get("fund", "")
        ctx["date_from"] = self.request.GET.get("date_from", "")
        ctx["date_to"] = self.request.GET.get("date_to", "")
        ctx["income_total"] = money(self.object_list.aggregate(s=Sum("amount"))["s"])
        return ctx


class IncomeCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Income
    form_class = IncomeForm
    template_name = "finance/income_form.html"
    success_url = reverse_lazy("finance:income")

    def get_modal_title(self):
        return "Add income"


class FundTransferListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = FundTransfer
    template_name = "finance/transfer_list.html"
    partial_template = "finance/partials/transfer_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        return FundTransfer.objects.select_related("from_fund", "to_fund").order_by("-date", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["transfer_total"] = money(
            self.object_list.aggregate(s=Sum("amount"))["s"]
        )
        ctx["transfer_count"] = self.object_list.count()
        return ctx


class FundTransferCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = FundTransfer
    form_class = FundTransferForm
    template_name = "finance/transfer_form.html"
    success_url = reverse_lazy("finance:transfers")

    def get_modal_title(self):
        return "Transfer between funds"
