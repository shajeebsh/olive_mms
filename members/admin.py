from django.contrib import admin

from .models import Family, Member


class MemberInline(admin.TabularInline):
    model = Member
    extra = 0
    fields = ["full_name", "phone", "email", "member_role", "membership_status"]


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ["name", "head", "phone", "email"]
    search_fields = ["name", "head", "phone", "email"]
    inlines = [MemberInline]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "family", "member_role", "membership_status", "phone", "join_date"]
    list_filter = ["membership_status", "member_role"]
    search_fields = ["full_name", "phone", "email", "family__name"]
