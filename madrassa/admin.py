from django.contrib import admin

from .models import Attendance, Class, Enrollment, Fee, FeePayment, Student


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    fields = ["madrassa_class", "academic_year", "status"]


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ["name", "level", "teacher", "schedule", "capacity", "is_active"]
    list_filter = ["is_active", "level"]
    search_fields = ["name", "level", "teacher__full_name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["full_name", "family", "guardian", "admission_date", "status"]
    list_filter = ["status"]
    search_fields = ["full_name", "guardian", "guardian_phone"]
    inlines = [EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "madrassa_class", "academic_year", "status"]
    list_filter = ["status", "madrassa_class"]
    search_fields = ["student__full_name", "madrassa_class__name"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["student", "madrassa_class", "date", "status"]
    list_filter = ["status", "date"]
    search_fields = ["student__full_name"]


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ["name", "amount", "frequency", "madrassa_class", "is_active"]
    list_filter = ["frequency", "is_active"]
    search_fields = ["name"]


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ["student", "fee", "amount", "date", "method", "receipt_number"]
    list_filter = ["method", "date"]
    search_fields = ["student__full_name", "receipt_number"]
