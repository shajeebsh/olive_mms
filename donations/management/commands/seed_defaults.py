from django.core.management.base import BaseCommand

from donations.models import DonationType
from finance.models import Fund

DONATION_TYPES = [
    ("SADQAH", "Sadaqah", "General"),
    ("ZAKAT", "Zakat", "Zakat"),
    ("LILLAH", "Lillah", "General"),
    ("FITRA", "Fitra", "Zakat"),
    ("QURBANI", "Qurbani", "General"),
    ("BUILDING", "Building Fund", "Building"),
    ("GENERAL", "General", "General"),
]

FUNDS = [
    ("General", "GEN", "General operating fund"),
    ("Zakat", "ZAK", "Zakat distribution fund"),
    ("Building", "BLD", "Building maintenance/construction"),
    ("Education", "EDU", "Madrassa education support"),
]


class Command(BaseCommand):
    help = "Seed default donation types and funds if they are missing."

    def handle(self, *args, **options):
        created_types = 0
        for code, name, hint in DONATION_TYPES:
            _, created = DonationType.objects.get_or_create(code=code, defaults={"name": name, "default_account_hint": hint})
            created_types += 1 if created else 0
        self.stdout.write(self.style.SUCCESS(f"Donation types ready ({created_types} created)."))

        created_funds = 0
        for name, code, hint in FUNDS:
            _, created = Fund.objects.get_or_create(code=code, defaults={"name": name})
            created_funds += 1 if created else 0
        self.stdout.write(self.style.SUCCESS(f"Funds ready ({created_funds} created)."))
