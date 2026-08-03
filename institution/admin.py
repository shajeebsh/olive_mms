from django.contrib import admin

from .models import MosqueProfile


@admin.register(MosqueProfile)
class MosqueProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "city", "phone", "email", "setup_complete", "updated_at"]
    search_fields = ["name", "city", "email"]
    readonly_fields = ["created_at", "updated_at"]
