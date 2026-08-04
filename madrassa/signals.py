from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FeePayment


@receiver(post_save, sender=FeePayment)
def post_fee_payment_to_fund(sender, instance, **kwargs):
    """Keep a matching finance.Income record in sync with each fee payment.

    Falls back to the Education fund (code EDU) when no fund is chosen.
    """
    from finance.models import Fund, Income

    fund = instance.fund
    if fund is None:
        fund = Fund.objects.filter(code="EDU").first()
    if fund is None:
        return

    Income.objects.update_or_create(
        fee_payment=instance,
        defaults={
            "fund": fund,
            "date": instance.date,
            "amount": instance.amount,
            "source": "Madrassa fee",
            "description": f"Fee {instance.receipt_number}",
        },
    )
