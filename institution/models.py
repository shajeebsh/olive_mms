from django.core.exceptions import ImproperlyConfigured
from django.db import models

from core.models import TimeStampedModel


class MosqueProfile(TimeStampedModel):
    name = models.CharField(max_length=200)
    tagline = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    bank_name = models.CharField("bank name", max_length=100, blank=True)
    bank_account = models.CharField("bank account", max_length=50, blank=True)
    bank_iban = models.CharField("IBAN", max_length=40, blank=True)
    hijri_offset = models.IntegerField(
        default=0,
        help_text="Days offset used by HIJRI helpers (store Gregorian dates in v1).",
    )
    enabled_modules = models.JSONField(default=list, blank=True)
    setup_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "mosque profile"
        verbose_name_plural = "mosque profiles"

    def __str__(self):
        return self.name

    @classmethod
    def get_solo(cls):
        """Return the singleton profile or None."""
        return cls.objects.first()

    @classmethod
    def get_solo_or_raise(cls):
        solo = cls.get_solo()
        if solo is None:
            raise ImproperlyConfigured("MosqueProfile has not been created yet — run setup.")
        return solo

    def save(self, *args, **kwargs):
        if self.pk is None and MosqueProfile.objects.exists():
            raise ImproperlyConfigured("Only one MosqueProfile is allowed (single tenant).")
        super().save(*args, **kwargs)
