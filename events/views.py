from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.mixins import HTMXDeleteMixin, HTMXModalFormMixin, HTMXPartialMixin

from .forms import EventAttendanceForm, EventForm
from .models import Event, EventAttendance


class EventListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Event
    template_name = "events/event_list.html"
    partial_template = "events/partials/event_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Event.objects.annotate(
            attendee_count=Count("attendees")
        ).order_by("-date_from")
        event_type = self.request.GET.get("event_type", "").strip()
        status = self.request.GET.get("status", "").strip()
        q = self.request.GET.get("q", "").strip()
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if status:
            queryset = queryset.filter(status=status)
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(location__icontains=q))
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["selected_type"] = self.request.GET.get("event_type", "")
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["q"] = self.request.GET.get("q", "")
        ctx["total_events"] = Event.objects.count()
        ctx["upcoming_events"] = Event.objects.filter(date_from__gte=date.today()).exclude(
            status=Event.Status.CANCELLED
        ).count()
        ctx["total_attendees"] = EventAttendance.objects.count()
        ctx["volunteer_count"] = EventAttendance.objects.filter(
            role=EventAttendance.Role.VOLUNTEER
        ).count()
        return ctx


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = "events/event_detail.html"

    def get_queryset(self):
        return Event.objects.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["attendees"] = self.object.attendees.select_related("member").order_by(
            "role", "member__full_name"
        )
        return ctx


class EventCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:index")

    def get_modal_title(self):
        return "Add event"


class EventUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:index")

    def get_modal_title(self):
        return f"Edit {self.object.name}"


class EventDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Event
    success_url = reverse_lazy("events:index")


class EventAttendanceCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = EventAttendance
    form_class = EventAttendanceForm
    template_name = "events/attendance_form.html"
    success_url = reverse_lazy("events:index")

    def get_initial(self):
        event_id = self.request.GET.get("event")
        return {"event": event_id} if event_id else {}

    def get_modal_title(self):
        return "Register attendee"


class EventAttendanceDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = EventAttendance
    success_url = reverse_lazy("events:index")


class VolunteerListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = EventAttendance
    template_name = "events/volunteer_list.html"
    partial_template = "events/partials/volunteer_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = EventAttendance.objects.select_related("event", "member").filter(
            role=EventAttendance.Role.VOLUNTEER
        ).order_by("-event__date_from", "member__full_name")
        event_id = self.request.GET.get("event", "").strip()
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["events"] = Event.objects.all()
        ctx["selected_event"] = self.request.GET.get("event", "")
        return ctx
