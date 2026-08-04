from datetime import date
from decimal import Decimal

from django.db import models

from core.models import TimeStampedModel


class Event(TimeStampedModel):
    class EventType(models.TextChoices):
        PRAYER = "PRAYER", "Prayer / Jummah"
        IFTAR = "IFTAR", "Iftar"
        EID = "EID", "Eid celebration"
        MADRASSA = "MADRASSA", "Madrassa / Class"
        FUNDRAISER = "FUNDRAISER", "Fundraiser"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    name = models.CharField(max_length=150)
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.OTHER)
    date_from = models.DateField(default=date.today)
    date_to = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=150, blank=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date_from"]

    def __str__(self):
        return self.name

    @property
    def attendees_count(self):
        return self.attendees.count()

    @property
    def volunteer_count(self):
        return self.attendees.filter(role=EventAttendance.Role.VOLUNTEER).count()


class EventAttendance(TimeStampedModel):
    class Role(models.TextChoices):
        ORGANIZER = "ORGANIZER", "Organizer"
        VOLUNTEER = "VOLUNTEER", "Volunteer"
        GUEST = "GUEST", "Guest"

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendees")
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        related_name="event_attendance",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.GUEST)

    class Meta:
        ordering = ["member__full_name"]
        constraints = [
            models.UniqueConstraint(fields=["event", "member"], name="unique_event_member")
        ]

    def __str__(self):
        return f"{self.member} @ {self.event} ({self.get_role_display()})"
