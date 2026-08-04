from django.contrib import admin

from .models import Category, Item, StockLevel, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "unit", "price", "low_stock_threshold", "is_active"]
    list_filter = ["is_active", "category"]
    search_fields = ["name", "unit"]


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ["item", "quantity"]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["item", "qty_change", "movement_type", "date", "purpose", "recipient"]
    list_filter = ["movement_type", "date"]
    search_fields = ["item__name", "purpose", "recipient__full_name", "recipient_name"]
