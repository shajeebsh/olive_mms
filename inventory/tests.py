from datetime import date
from decimal import Decimal

from django.test import TestCase

from members.models import Member

from .forms import DistributionForm, StockMovementForm
from .models import Category, Item, StockLevel, StockMovement


class StockSyncTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Rice", unit="kg", price=Decimal("2.50"))

    def test_stock_in_updates_level(self):
        StockMovement.objects.create(
            item=self.item, qty_change=Decimal("100"), movement_type=StockMovement.MovementType.IN
        )
        self.assertEqual(StockLevel.objects.get(item=self.item).quantity, Decimal("100"))

    def test_stock_out_updates_level(self):
        StockMovement.objects.create(
            item=self.item, qty_change=Decimal("100"), movement_type=StockMovement.MovementType.IN
        )
        StockMovement.objects.create(
            item=self.item, qty_change=Decimal("40"), movement_type=StockMovement.MovementType.OUT
        )
        self.assertEqual(StockLevel.objects.get(item=self.item).quantity, Decimal("60"))

    def test_delete_movement_recomputes(self):
        StockMovement.objects.create(
            item=self.item, qty_change=Decimal("100"), movement_type=StockMovement.MovementType.IN
        )
        outgoing = StockMovement.objects.create(
            item=self.item, qty_change=Decimal("30"), movement_type=StockMovement.MovementType.OUT
        )
        outgoing.delete()
        self.assertEqual(StockLevel.objects.get(item=self.item).quantity, Decimal("100"))


class ItemModelTests(TestCase):
    def test_is_low_stock(self):
        item = Item.objects.create(
            name="Dates", unit="box", low_stock_threshold=Decimal("10")
        )
        StockMovement.objects.create(
            item=item, qty_change=Decimal("5"), movement_type=StockMovement.MovementType.IN
        )
        self.assertTrue(item.is_low_stock)

    def test_stock_value(self):
        item = Item.objects.create(name="Water", unit="bottle", price=Decimal("1.00"))
        StockMovement.objects.create(
            item=item, qty_change=Decimal("8"), movement_type=StockMovement.MovementType.IN
        )
        self.assertEqual(item.stock_value, Decimal("8.00"))


class StockMovementFormTests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Milk", unit="L", price=Decimal("1.50"))

    def test_out_requires_recipient(self):
        form = StockMovementForm(
            data={
                "item": self.item.pk,
                "movement_type": StockMovement.MovementType.OUT,
                "qty_change": "2",
                "date": date(2026, 8, 4),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("recipient", form.errors["__all__"][0])

    def test_out_enough_stock(self):
        StockMovement.objects.create(
            item=self.item, qty_change=Decimal("10"), movement_type=StockMovement.MovementType.IN
        )
        member = Member.objects.create(full_name="Hamza Yusuf")
        form = StockMovementForm(
            data={
                "item": self.item.pk,
                "movement_type": StockMovement.MovementType.OUT,
                "qty_change": "2",
                "date": date(2026, 8, 4),
                "recipient": member.pk,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_out_insufficient_stock_rejected(self):
        StockMovement.objects.create(
            item=self.item, qty_change=Decimal("1"), movement_type=StockMovement.MovementType.IN
        )
        member = Member.objects.create(full_name="Zaynab Ali")
        form = StockMovementForm(
            data={
                "item": self.item.pk,
                "movement_type": StockMovement.MovementType.OUT,
                "qty_change": "5",
                "date": date(2026, 8, 4),
                "recipient": member.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("stock", form.errors["__all__"][0])

    def test_distribution_form_forces_out(self):
        StockMovement.objects.create(
            item=self.item, qty_change=Decimal("10"), movement_type=StockMovement.MovementType.IN
        )
        member = Member.objects.create(full_name="Khadija Omar")
        form = DistributionForm(
            data={
                "item": self.item.pk,
                "qty_change": "3",
                "date": date(2026, 8, 4),
                "recipient": member.pk,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["movement_type"], StockMovement.MovementType.OUT)
