from django.contrib import admin

from .models import Expense, Fund, FundTransfer, Income


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "opening_balance", "is_active"]
    search_fields = ["name", "code"]


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ["fund", "date", "amount", "source", "donation", "fee_payment"]
    list_filter = ["fund", "date"]
    search_fields = ["source", "description"]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["fund", "date", "amount", "category", "payee", "status"]
    list_filter = ["fund", "status", "date"]
    search_fields = ["category", "description", "payee"]


@admin.register(FundTransfer)
class FundTransferAdmin(admin.ModelAdmin):
    list_display = ["from_fund", "to_fund", "amount", "date"]
    list_filter = ["date"]
