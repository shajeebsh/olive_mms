from datetime import date

from django.db import models

from core.models import TimeStampedModel


class DonationType(TimeStampedModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    default_account_hint = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Donation(TimeStampedModel):
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        BANK = "BANK", "Bank transfer"
        ONLINE = "ONLINE", "Online"

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
    )
    donation_type = models.ForeignKey(DonationType, on_delete=models.PROTECT, related_name="donations")
    fund = models.ForeignKey("finance.Fund", on_delete=models.PROTECT, related_name="donations")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    date = models.DateField(default=date.today)
    reference_no = models.CharField(max_length=50, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.donation_type} {self.amount} on {self.date}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            daily_count = Donation.objects.filter(date=self.date).count() + 1
            self.receipt_number = f"RCP-{self.date:%Y%m%d}-{daily_count:04d}"
        super().save(*args, **kwargs)


class Pledge(TimeStampedModel):
    class Frequency(models.TextChoices):
        ONCE = "ONCE", "One-time"
        MONTHLY = "MONTHLY", "Monthly"
        ANNUAL = "ANNUAL", "Annual"

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        related_name="pledges",
    )
    donation_type = models.ForeignKey(DonationType, on_delete=models.PROTECT, related_name="pledges")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-is_active", "-start_date"]

    def __str__(self):
        return f"{self.member} {self.donation_type} {self.amount}"
