from django.contrib import admin

from .models import Donation, DonationType, Pledge


@admin.register(DonationType)
class DonationTypeAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "default_account_hint"]
    search_fields = ["code", "name"]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["receipt_number", "date", "member", "donation_type", "fund", "amount", "payment_method"]
    list_filter = ["donation_type", "fund", "payment_method", "date"]
    search_fields = ["receipt_number", "reference_no", "member__full_name"]


@admin.register(Pledge)
class PledgeAdmin(admin.ModelAdmin):
    list_display = ["member", "donation_type", "amount", "frequency", "is_active"]
    list_filter = ["frequency", "is_active"]
    search_fields = ["member__full_name"]
