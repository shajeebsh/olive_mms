from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from core.mixins import HTMXDeleteMixin, HTMXModalFormMixin, HTMXPartialMixin

from .forms import FamilyForm, MemberForm
from .models import Family, Member


class MemberListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Member
    template_name = "members/member_list.html"
    partial_template = "members/partials/member_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Member.objects.select_related("family").order_by("full_name")
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(full_name__icontains=q)
                | Q(phone__icontains=q)
                | Q(email__icontains=q)
                | Q(family__name__icontains=q)
            )
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["total_members"] = Member.objects.count()
        ctx["active_members"] = Member.objects.filter(membership_status=Member.MembershipStatus.ACTIVE).count()
        ctx["families_count"] = Family.objects.count()
        ctx["volunteers_count"] = Member.objects.filter(member_role=Member.MemberRole.VOLUNTEER).count()
        return ctx


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "members/member_detail.html"

    def get_queryset(self):
        return Member.objects.select_related("family")


class MemberCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Member
    form_class = MemberForm
    template_name = "members/member_form.html"
    success_url = reverse_lazy("members:index")

    def get_modal_title(self):
        return "Add member"


class MemberUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Member
    form_class = MemberForm
    template_name = "members/member_form.html"
    success_url = reverse_lazy("members:index")

    def get_modal_title(self):
        return f"Edit {self.object.full_name}"


class MemberDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Member
    success_url = reverse_lazy("members:index")


class FamilyListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Family
    template_name = "members/family_list.html"
    partial_template = "members/partials/family_list_content.html"
    paginate_by = 25

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        return ctx

    def get_queryset(self):
        queryset = Family.objects.annotate(member_count=Count("members")).order_by("name")
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(head__icontains=q))
        return queryset


class FamilyDetailView(LoginRequiredMixin, DetailView):
    model = Family
    template_name = "members/family_detail.html"


class FamilyCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Family
    form_class = FamilyForm
    template_name = "members/family_form.html"
    success_url = reverse_lazy("members:family_list")

    def get_modal_title(self):
        return "Add family"


class FamilyUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Family
    form_class = FamilyForm
    template_name = "members/family_form.html"
    success_url = reverse_lazy("members:family_list")

    def get_modal_title(self):
        return f"Edit {self.object.name}"


class FamilyDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Family
    success_url = reverse_lazy("members:family_list")
