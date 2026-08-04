from datetime import date
from decimal import Decimal

from django.db import models

from core.models import TimeStampedModel
from core.utils import money


class Category(TimeStampedModel):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Item(TimeStampedModel):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
    )
    unit = models.CharField(max_length=30, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    low_stock_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def quantity(self):
        level = getattr(self, "stock_level", None)
        return level.quantity if level else Decimal("0")

    @property
    def is_low_stock(self):
        return self.is_active and self.quantity <= self.low_stock_threshold

    @property
    def stock_value(self):
        return money(self.quantity * self.price)


class StockLevel(TimeStampedModel):
    item = models.OneToOneField(Item, on_delete=models.CASCADE, related_name="stock_level")
    quantity = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0"))

    def __str__(self):
        return f"{self.item}: {self.quantity}"


class StockMovement(TimeStampedModel):
    class MovementType(models.TextChoices):
        IN = "IN", "Stock in"
        OUT = "OUT", "Distribution / out"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="movements")
    qty_change = models.DecimalField(max_digits=14, decimal_places=2)
    movement_type = models.CharField(max_length=10, choices=MovementType.choices)
    date = models.DateField(default=date.today)
    purpose = models.CharField(max_length=150, blank=True)
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    recipient = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="distributions",
    )
    recipient_name = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.qty_change} {self.item} on {self.date}"

    @property
    def recipient_display(self):
        if self.recipient:
            return self.recipient.full_name
        return self.recipient_name or "—"
