from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from members.models import Member

from .models import Event, EventAttendance


class EventModelTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Ramadan Iftar",
            event_type=Event.EventType.IFTAR,
            date_from=date(2026, 3, 10),
        )
        self.member = Member.objects.create(full_name="Bilal Khan")

    def test_attendance_registered(self):
        attendance = EventAttendance.objects.create(
            event=self.event, member=self.member, role=EventAttendance.Role.GUEST
        )
        self.assertEqual(self.event.attendees_count, 1)
        self.assertEqual(self.event.attendees.get(pk=attendance.pk).member, self.member)

    def test_unique_event_member_constraint(self):
        EventAttendance.objects.create(
            event=self.event, member=self.member, role=EventAttendance.Role.GUEST
        )
        with self.assertRaises(Exception):
            EventAttendance.objects.create(
                event=self.event, member=self.member, role=EventAttendance.Role.VOLUNTEER
            )

    def test_volunteer_count(self):
        EventAttendance.objects.create(
            event=self.event, member=self.member, role=EventAttendance.Role.VOLUNTEER
        )
        volunteer = Member.objects.create(full_name="Aisha Ali")
        EventAttendance.objects.create(
            event=self.event, member=volunteer, role=EventAttendance.Role.VOLUNTEER
        )
        guest = Member.objects.create(full_name="Umar Farooq")
        EventAttendance.objects.create(
            event=self.event, member=guest, role=EventAttendance.Role.GUEST
        )
        self.assertEqual(self.event.volunteer_count, 2)
        self.assertEqual(self.event.attendees_count, 3)


class EventViewTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(name="Jummah Khutbah", event_type=Event.EventType.PRAYER)
        User = get_user_model()
        self.user = User.objects.create_user(
            email="tester@example.com", password="testpass", full_name="Tester"
        )

    def test_list_requires_login(self):
        response = self.client.get("/events/")
        self.assertEqual(response.status_code, 302)

    def test_list_shows_events(self):
        self.client.login(email="tester@example.com", password="testpass")
        response = self.client.get("/events/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jummah Khutbah")
