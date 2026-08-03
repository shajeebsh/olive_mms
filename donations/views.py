from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.mixins import HTMXDeleteMixin, HTMXModalFormMixin, HTMXPartialMixin
from core.utils import money

from .forms import DonationForm, DonationTypeForm, PledgeForm
from .models import Donation, DonationType, Pledge


class DonationListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Donation
    template_name = "donations/donation_list.html"
    partial_template = "donations/partials/donation_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Donation.objects.select_related("member", "donation_type", "fund").order_by("-date", "-id")
        filters = Q()
        donation_type = self.request.GET.get("donation_type", "").strip()
        payment_method = self.request.GET.get("payment_method", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        q = self.request.GET.get("q", "").strip()
        if donation_type:
            filters &= Q(donation_type_id=donation_type)
        if payment_method:
            filters &= Q(payment_method=payment_method)
        if date_from:
            filters &= Q(date__gte=date_from)
        if date_to:
            filters &= Q(date__lte=date_to)
        if q:
            filters &= Q(member__full_name__icontains=q) | Q(receipt_number__icontains=q) | Q(reference_no__icontains=q)
        return queryset.filter(filters)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        filtered = self.object_list
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_type"] = self.request.GET.get("donation_type", "")
        ctx["selected_method"] = self.request.GET.get("payment_method", "")
        ctx["date_from"] = self.request.GET.get("date_from", "")
        ctx["date_to"] = self.request.GET.get("date_to", "")
        ctx["donation_types"] = DonationType.objects.filter(is_active=True)
        ctx["filtered_total"] = money(filtered.aggregate(s=Sum("amount"))["s"])
        ctx["total_donations"] = money(Donation.objects.aggregate(s=Sum("amount"))["s"])
        month_start = date.today().replace(day=1)
        ctx["month_total"] = money(
            Donation.objects.filter(date__gte=month_start).aggregate(s=Sum("amount"))["s"]
        )
        ctx["donation_count"] = Donation.objects.count()
        return ctx


class DonationDetailView(LoginRequiredMixin, DetailView):
    model = Donation
    template_name = "donations/donation_detail.html"

    def get_queryset(self):
        return Donation.objects.select_related("member", "donation_type", "fund")


class DonationReceiptView(LoginRequiredMixin, DetailView):
    model = Donation
    template_name = "donations/receipt.html"

    def get_queryset(self):
        return Donation.objects.select_related("member", "donation_type", "fund")


class DonationCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Donation
    form_class = DonationForm
    template_name = "donations/donation_form.html"
    success_url = reverse_lazy("donations:index")

    def get_modal_title(self):
        return "Record donation"


class DonationUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Donation
    form_class = DonationForm
    template_name = "donations/donation_form.html"
    success_url = reverse_lazy("donations:index")

    def get_modal_title(self):
        return f"Edit donation {self.object.receipt_number}"


class DonationDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Donation
    success_url = reverse_lazy("donations:index")


class PledgeListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Pledge
    template_name = "donations/pledge_list.html"
    partial_template = "donations/partials/pledge_list_content.html"

    def get_queryset(self):
        return Pledge.objects.select_related("member", "donation_type").order_by("-is_active", "-start_date")


class PledgeCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Pledge
    form_class = PledgeForm
    template_name = "donations/pledge_form.html"
    success_url = reverse_lazy("donations:pledges")

    def get_modal_title(self):
        return "Add pledge"


class DonationTypeListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = DonationType
    template_name = "donations/donationtype_list.html"
    partial_template = "donations/partials/donationtype_list_content.html"


class DonationTypeCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = DonationType
    form_class = DonationTypeForm
    template_name = "donations/donationtype_form.html"
    success_url = reverse_lazy("donations:types")

    def get_modal_title(self):
        return "Add donation type"
