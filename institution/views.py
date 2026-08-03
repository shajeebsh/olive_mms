from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from core.mixins import HTMXModalFormMixin, HTMXPartialMixin

from .forms import MosqueProfileForm
from .models import MosqueProfile


class IndexView(LoginRequiredMixin, HTMXPartialMixin, TemplateView):
    template_name = "institution/index.html"
    partial_template = "institution/partials/index_content.html"

    def dispatch(self, request, *args, **kwargs):
        if not MosqueProfile.objects.exists():
            return redirect("institution:setup")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["profile"] = MosqueProfile.get_solo()
        return ctx


class SetupView(LoginRequiredMixin, CreateView):
    model = MosqueProfile
    form_class = MosqueProfileForm
    template_name = "institution/mosqueprofile_form.html"
    success_url = reverse_lazy("institution:index")

    def dispatch(self, request, *args, **kwargs):
        if MosqueProfile.objects.exists():
            return redirect("institution:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.setup_complete = True
        return super().form_valid(form)


class ProfileEditView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = MosqueProfile
    form_class = MosqueProfileForm
    template_name = "institution/mosqueprofile_form.html"
    success_url = reverse_lazy("institution:index")

    def get_object(self, queryset=None):
        profile = MosqueProfile.get_solo()
        if profile is None:
            raise Http404("No mosque profile yet — run setup first.")
        return profile

    def get_modal_title(self):
        return "Edit mosque profile"
