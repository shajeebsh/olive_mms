from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Donation


@receiver(post_save, sender=Donation)
def post_donation_to_fund(sender, instance, **kwargs):
    """Keep a matching finance.Income record in sync with each donation."""
    from finance.models import Income

    Income.objects.update_or_create(
        donation=instance,
        defaults={
            "fund_id": instance.fund_id,
            "date": instance.date,
            "amount": instance.amount,
            "source": str(instance.donation_type),
            "description": f"Donation {instance.receipt_number}",
        },
    )
