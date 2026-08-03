from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from django.apps import apps


def get_current_mosque(request):
    """Return the MosqueProfile singleton, or None until setup completes."""
    try:
        MosqueProfile = apps.get_model("institution", "MosqueProfile")
    except LookupError:
        return None
    return MosqueProfile.get_solo()


def money(value):
    """Round an amount to 2 decimal places, guarding SQLite float artifacts in aggregates."""
    try:
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (TypeError, ValueError, InvalidOperation):
        return Decimal("0.00")
