from django.db.models import Q, Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import StockLevel, StockMovement


def _recompute_stock(item_id):
    """Recalculate an item's StockLevel from all of its movements."""
    aggregate = StockMovement.objects.filter(item_id=item_id).aggregate(
        stock_in=Sum("qty_change", filter=Q(movement_type=StockMovement.MovementType.IN)),
        stock_out=Sum("qty_change", filter=Q(movement_type=StockMovement.MovementType.OUT)),
    )
    quantity = (aggregate["stock_in"] or 0) - (aggregate["stock_out"] or 0)
    StockLevel.objects.update_or_create(item_id=item_id, defaults={"quantity": quantity})


@receiver(post_save, sender=StockMovement)
def sync_stock_on_save(sender, instance, **kwargs):
    _recompute_stock(instance.item_id)


@receiver(post_delete, sender=StockMovement)
def sync_stock_on_delete(sender, instance, **kwargs):
    _recompute_stock(instance.item_id)
