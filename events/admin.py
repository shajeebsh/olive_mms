from django.contrib import admin

from .models import Event, EventAttendance


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["name", "event_type", "date_from", "date_to", "location", "budget", "status"]
    list_filter = ["event_type", "status", "date_from"]
    search_fields = ["name", "location"]


@admin.register(EventAttendance)
class EventAttendanceAdmin(admin.ModelAdmin):
    list_display = ["event", "member", "role"]
    list_filter = ["role", "event"]
    search_fields = ["event__name", "member__full_name"]
