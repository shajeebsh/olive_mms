from datetime import date
from decimal import Decimal

from django.db import models

from core.models import TimeStampedModel
from core.utils import money


class Fund(TimeStampedModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def balance(self):
        income = self.incomes.aggregate(s=models.Sum("amount"))["s"] or Decimal("0")
        expense = self.expenses.aggregate(s=models.Sum("amount"))["s"] or Decimal("0")
        transfers_in = self.transfers_in.aggregate(s=models.Sum("amount"))["s"] or Decimal("0")
        transfers_out = self.transfers_out.aggregate(s=models.Sum("amount"))["s"] or Decimal("0")
        return money(self.opening_balance + income + transfers_in - expense - transfers_out)


class Income(TimeStampedModel):
    fund = models.ForeignKey(Fund, on_delete=models.PROTECT, related_name="incomes")
    date = models.DateField(default=date.today)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=100, blank=True)
    donation = models.OneToOneField(
        "donations.Donation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="income",
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name_plural = "income"

    def __str__(self):
        return f"{self.fund} +{self.amount} on {self.date}"


class Expense(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    fund = models.ForeignKey(Fund, on_delete=models.PROTECT, related_name="expenses")
    date = models.DateField(default=date.today)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=255, blank=True)
    payee = models.CharField(max_length=150, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.fund} -{self.amount} on {self.date}"


class FundTransfer(TimeStampedModel):
    from_fund = models.ForeignKey(Fund, on_delete=models.PROTECT, related_name="transfers_out")
    to_fund = models.ForeignKey(Fund, on_delete=models.PROTECT, related_name="transfers_in")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=date.today)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.from_fund} -> {self.to_fund} {self.amount}"
