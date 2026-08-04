"""Seed a small, realistic demo dataset across all modules for testing/UX review."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from donations.models import Donation, DonationType, Pledge
from events.models import Event, EventAttendance
from finance.models import Expense, Fund, FundTransfer
from inventory.models import Category, Item, StockMovement
from madrassa.models import Class, Enrollment, Fee, FeePayment, Student
from members.models import Family, Member


def today_minus(days):
    return date.today() - timedelta(days=days)


class Command(BaseCommand):
    help = "Seed demo data across members, donations, finance, madrassa, events, and inventory."

    def handle(self, *args, **options):
        from donations.management.commands.seed_defaults import Command as SeedDefaults

        SeedDefaults().handle()

        general_fund = Fund.objects.get(code="GEN")
        zakat_fund = Fund.objects.get(code="ZAK")

        self.families()
        members = self.members()
        classes = self.madrassa(members)
        self.donations(members)
        self.finance(members, general_fund, zakat_fund)
        event = self.events(members)
        self.inventory(general_fund, event)
        self.fee_payments(classes, members)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))

    def families(self):
        Family.objects.get_or_create(name="Khan Family")
        Family.objects.get_or_create(name="Ahmed Family")
        Family.objects.get_or_create(name="Hussain Family")

    def members(self):
        defaults = [
            ("Imam Yusuf Rahman", "IMAM", "Active", "khan"),
            ("Ustadh Karim Ali", "TEACHER", "Active", "khan"),
            ("Abdul Qadir", "DONOR", "Active", "ahmed"),
            ("Fatima Zahra", "VOLUNTEER", "Active", "ahmed"),
            ("Hassan Ahmed", "MEMBER", "Active", "hussain"),
            ("Maryam Siddiq", "MEMBER", "Friend", "hussain"),
        ]
        created = []
        for name, role, status, family_key in defaults:
            family = Family.objects.get(name__startswith=family_key.title())
            member, _ = Member.objects.get_or_create(
                email=name.lower().replace(" ", ".") + "@example.com",
                defaults={
                    "full_name": name,
                    "family": family,
                    "phone": "07123 456789",
                    "join_date": today_minus(400),
                    "membership_status": status,
                    "member_role": role,
                },
            )
            created.append(member)
        return created

    def madrassa(self, members):
        teacher = Member.objects.filter(member_role="TEACHER").first() or members[1]
        hifz = Class.objects.get_or_create(name="Hifz 1", level="Beginner", teacher=teacher)[0]
        qaida = Class.objects.get_or_create(name="Qaida", level="Foundation", teacher=teacher)[0]
        fee = Fee.objects.get_or_create(name="Monthly tuition", amount=Decimal("100.00"), frequency="MONTHLY")[0]

        year = str(date.today().year)
        for i, (name, cls) in enumerate([("Adam Ismail", hifz), ("Noor Begum", hifz), ("Yusuf Farid", qaida)]):
            student = Student.objects.get_or_create(
                full_name=name,
                defaults={
                    "family": Family.objects.first(),
                    "guardian": "Parent of " + name,
                    "guardian_phone": "07111 222333",
                    "admission_date": today_minus(300),
                },
            )[0]
            Enrollment.objects.get_or_create(
                student=student, madrassa_class=cls, academic_year=year, status="ENROLLED"
            )
        return [hifz, qaida]

    def donations(self, members):
        donor = Member.objects.filter(member_role="DONOR").first() or members[2]
        zakat = DonationType.objects.get(code="ZAKAT")
        general = DonationType.objects.get(code="GENERAL")
        zakat_fund = Fund.objects.get(code="ZAK")
        general_fund = Fund.objects.get(code="GEN")
        for i in range(3):
            Donation.objects.create(
                member=donor,
                donation_type=zakat,
                fund=zakat_fund,
                amount=Decimal("200.00") + Decimal(i) * 100,
                date=today_minus(i * 12),
            )
        Donation.objects.create(
            member=donor,
            donation_type=general,
            fund=general_fund,
            amount=Decimal("150.00"),
            date=today_minus(20),
        )
        Pledge.objects.get_or_create(
            member=donor,
            donation_type=general,
            amount=Decimal("50.00"),
            frequency="MONTHLY",
            start_date=date.today(),
        )

    def finance(self, members, general_fund, zakat_fund):
        Expense.objects.create(
            fund=general_fund, amount=Decimal("80.00"), category="Utilities",
            description="Electricity bill", payee="Council", status="APPROVED", date=today_minus(10),
        )
        Expense.objects.create(
            fund=general_fund, amount=Decimal("120.00"), category="Maintenance",
            description="Carpet cleaning", payee="Clean Co", status="PENDING", date=today_minus(4),
        )
        FundTransfer.objects.create(
            from_fund=general_fund, to_fund=zakat_fund, amount=Decimal("300.00"),
            date=today_minus(8), note="Monthly allocation",
        )

    def events(self, members):
        event = Event.objects.create(
            name="Ramadan Iftar", event_type="IFTAR",
            date_from=date.today() + timedelta(days=15),
            location="Main hall", budget=Decimal("500.00"), status="PLANNED",
        )
        completed = Event.objects.create(
            name="Friday Jummah", event_type="PRAYER",
            date_from=today_minus(3), status="COMPLETED",
        )
        for member in members[:4]:
            EventAttendance.objects.get_or_create(event=event, member=member, role="VOLUNTEER")
        for member in members[4:]:
            EventAttendance.objects.get_or_create(event=completed, member=member, role="GUEST")
        return event

    def inventory(self, general_fund, event):
        foods = Category.objects.get_or_create(name="Food Items")[0]
        supplies = Category.objects.get_or_create(name="General Supplies")[0]
        rice = Item.objects.get_or_create(
            name="Basmati Rice (10kg)",
            defaults={"category": foods, "unit": "bag", "price": Decimal("45.00"),
                      "low_stock_threshold": Decimal("5")},
        )[0]
        oil = Item.objects.get_or_create(
            name="Cooking Oil (1L)",
            defaults={"category": foods, "unit": "bottle", "price": Decimal("6.50"),
                      "low_stock_threshold": Decimal("12")},
        )[0]
        StockMovement.objects.create(
            item=rice, qty_change=Decimal("20"), movement_type="IN",
            purpose="Opening stock", date=today_minus(30),
        )
        StockMovement.objects.create(
            item=oil, qty_change=Decimal("30"), movement_type="IN",
            purpose="Opening stock", date=today_minus(30),
        )
        StockMovement.objects.create(
            item=rice, qty_change=Decimal("3"), movement_type="OUT",
            purpose="Iftar cooking",
            recipient=Member.objects.filter(member_role="VOLUNTEER").first(),
            event=event, date=today_minus(1),
        )
        return [rice, oil]

    def fee_payments(self, classes, members):
        year = str(date.today().year)
        fee = Fee.objects.get(name="Monthly tuition")
        for student in Student.objects.all():
            FeePayment.objects.create(
                student=student, fee=fee, amount=Decimal("100.00"),
                date=today_minus(5), method="CASH",
            )
