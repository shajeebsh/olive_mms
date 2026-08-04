from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from core.mixins import HTMXDeleteMixin, HTMXModalFormMixin, HTMXPartialMixin
from core.utils import money

from .forms import ClassForm, EnrollmentForm, FeeForm, FeePaymentForm, StudentForm
from .models import Attendance, Class, Enrollment, Fee, FeePayment, Student


class MadrassaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "madrassa/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["student_count"] = Student.objects.count()
        ctx["active_students"] = Student.objects.filter(status=Student.Status.ACTIVE).count()
        ctx["class_count"] = Class.objects.count()
        ctx["active_enrollments"] = Enrollment.objects.filter(status=Enrollment.Status.ENROLLED).count()

        today = date.today()
        ctx["month_fees"] = money(
            FeePayment.objects.filter(date__year=today.year, date__month=today.month).aggregate(
                s=Sum("amount")
            )["s"]
        )
        ctx["classes"] = Class.objects.annotate(
            enrolled=Count("enrollments", filter=Q(enrollments__status=Enrollment.Status.ENROLLED))
        ).order_by("name")
        ctx["recent_payments"] = FeePayment.objects.select_related("student", "fee").order_by(
            "-date", "-id"
        )[:5]
        return ctx


class ClassListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Class
    template_name = "madrassa/class_list.html"
    partial_template = "madrassa/partials/class_list_content.html"

    def get_queryset(self):
        return Class.objects.select_related("teacher").annotate(
            enrolled=Count("enrollments", filter=Q(enrollments__status=Enrollment.Status.ENROLLED))
        ).order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_classes"] = self.object_list.filter(is_active=True).count()
        ctx["student_count"] = Student.objects.filter(status=Student.Status.ACTIVE).count()
        return ctx


class ClassCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Class
    form_class = ClassForm
    template_name = "madrassa/class_form.html"
    success_url = reverse_lazy("madrassa:classes")

    def get_modal_title(self):
        return "Add class"


class ClassUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Class
    form_class = ClassForm
    template_name = "madrassa/class_form.html"
    success_url = reverse_lazy("madrassa:classes")

    def get_modal_title(self):
        return f"Edit {self.object.name}"


class ClassDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Class
    success_url = reverse_lazy("madrassa:classes")


class StudentListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Student
    template_name = "madrassa/student_list.html"
    partial_template = "madrassa/partials/student_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Student.objects.select_related("family", "member").order_by("full_name")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        if q:
            queryset = queryset.filter(
                Q(full_name__icontains=q)
                | Q(guardian__icontains=q)
                | Q(guardian_phone__icontains=q)
                | Q(family__name__icontains=q)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["total_students"] = Student.objects.count()
        ctx["active_students"] = Student.objects.filter(status=Student.Status.ACTIVE).count()
        ctx["graduated_students"] = Student.objects.filter(status=Student.Status.GRADUATED).count()
        ctx["active_enrollments"] = Enrollment.objects.filter(status=Enrollment.Status.ENROLLED).count()
        return ctx


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = "madrassa/student_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        student = self.object
        ctx["enrollments"] = student.enrollments.select_related("madrassa_class").order_by(
            "-academic_year"
        )
        ctx["recent_payments"] = student.fee_payments.select_related("fee").order_by("-date")[:10]
        ctx["attendance_count"] = student.attendance_records.count()
        ctx["attendance_present"] = student.attendance_records.filter(
            status=Attendance.Status.PRESENT
        ).count()
        return ctx


class StudentCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = "madrassa/student_form.html"
    success_url = reverse_lazy("madrassa:students")

    def get_modal_title(self):
        return "Add student"


class StudentUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "madrassa/student_form.html"
    success_url = reverse_lazy("madrassa:students")

    def get_modal_title(self):
        return f"Edit {self.object.full_name}"


class StudentDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Student
    success_url = reverse_lazy("madrassa:students")


class EnrollmentListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Enrollment
    template_name = "madrassa/enrollment_list.html"
    partial_template = "madrassa/partials/enrollment_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Enrollment.objects.select_related("student", "madrassa_class").order_by(
            "-academic_year", "student__full_name"
        )
        class_id = self.request.GET.get("class_id", "").strip()
        status = self.request.GET.get("status", "").strip()
        if class_id:
            queryset = queryset.filter(madrassa_class_id=class_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = Class.objects.filter(is_active=True).order_by("name")
        ctx["selected_class"] = self.request.GET.get("class_id", "")
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["total_enrollments"] = Enrollment.objects.count()
        ctx["active_enrollments"] = Enrollment.objects.filter(status=Enrollment.Status.ENROLLED).count()
        return ctx


class EnrollmentCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = "madrassa/enrollment_form.html"
    success_url = reverse_lazy("madrassa:enrollments")

    def get_modal_title(self):
        return "Enroll student"


class EnrollmentUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = "madrassa/enrollment_form.html"
    success_url = reverse_lazy("madrassa:enrollments")

    def get_modal_title(self):
        return f"Edit {self.object.student}"


class EnrollmentDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Enrollment
    success_url = reverse_lazy("madrassa:enrollments")


class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendance
    template_name = "madrassa/attendance.html"
    grid_partial = "madrassa/partials/attendance_grid.html"
    paginate_by = 25

    def get_template_names(self):
        if self.request.GET.get("grid") == "1":
            return [self.grid_partial]
        return [self.template_name]

    def get_queryset(self):
        queryset = Attendance.objects.select_related("student", "madrassa_class").order_by(
            "-date", "student__full_name"
        )
        class_id = self.request.GET.get("class_id", "").strip()
        date_str = self.request.GET.get("date", "").strip()
        if class_id:
            queryset = queryset.filter(madrassa_class_id=class_id)
        if date_str:
            queryset = queryset.filter(date=date_str)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = Class.objects.filter(is_active=True).order_by("name")
        ctx["selected_class"] = self.request.GET.get("class_id", "")
        date_str = self.request.GET.get("date", "").strip()
        ctx["selected_date"] = date_str or date.today().isoformat()

        day_attendance = Attendance.objects.filter(date=ctx["selected_date"])
        if ctx["selected_class"]:
            day_attendance = day_attendance.filter(madrassa_class_id=ctx["selected_class"])
        ctx["present_today"] = day_attendance.filter(status=Attendance.Status.PRESENT).count()
        ctx["late_today"] = day_attendance.filter(status=Attendance.Status.LATE).count()
        total_today = day_attendance.count()
        ctx["absent_today"] = day_attendance.filter(status=Attendance.Status.ABSENT).count()
        ctx["attendance_rate"] = 0
        if total_today:
            ctx["attendance_rate"] = round(
                (day_attendance.filter(status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]).count())
                / total_today * 100,
                1,
            )

        ctx["grid_rows"] = self.grid_rows(ctx["selected_class"], ctx["selected_date"])

        selected_day = date.fromisoformat(ctx["selected_date"])
        ctx["prev_date"] = (selected_day - timedelta(days=1)).isoformat()
        ctx["next_date"] = (selected_day + timedelta(days=1)).isoformat()
        return ctx

    def grid_rows(self, class_id, date_str):
        """Students enrolled in the class (or all active students) plus their status for the day."""
        if class_id:
            student_ids = list(
                Enrollment.objects.filter(
                    madrassa_class_id=class_id, status=Enrollment.Status.ENROLLED
                ).values_list("student_id", flat=True)
            )
            students = Student.objects.filter(id__in=student_ids).order_by("full_name")
        else:
            students = Student.objects.filter(status=Student.Status.ACTIVE).order_by("full_name")
        existing = {
            a.student_id: a
            for a in Attendance.objects.filter(
                student__in=students, date=date_str
            ).select_related("student")
        }
        rows = []
        for student in students:
            record = existing.get(student.pk)
            rows.append(
                {
                    "student": student,
                    "status": record.status if record else None,
                    "record_id": record.pk if record else None,
                }
            )
        return rows


class AttendanceSetView(LoginRequiredMixin, View):
    """Quick check-in: create or update one student's attendance for a date."""

    def post(self, request, *args, **kwargs):
        student_id = request.POST.get("student_id")
        date_str = request.POST.get("date")
        status = request.POST.get("status")
        class_id = request.POST.get("class_id", "").strip() or None
        try:
            date_obj = parse_date(date_str) or date.today()
            student = Student.objects.get(pk=student_id)
            if status not in Attendance.Status.values:
                raise ValidationError("Invalid status")
        except (Student.DoesNotExist, ValidationError, TypeError):
            return HttpResponse(status=400)
        Attendance.objects.update_or_create(
            student=student,
            date=date_obj,
            defaults={
                "status": status,
                "madrassa_class_id": class_id,
            },
        )
        return HttpResponse(
            "",
            status=204,
            headers={"HX-Trigger": '"attendanceChanged"'},
        )


class AttendanceMarkAllView(LoginRequiredMixin, View):
    """Mark every enrolled student in a class as present for the given date."""

    def post(self, request, *args, **kwargs):
        class_id = request.POST.get("class_id", "").strip()
        date_str = request.POST.get("date")
        try:
            date_obj = parse_date(date_str) or date.today()
        except (TypeError, ValueError):
            return HttpResponse(status=400)
        student_ids = list(
            Enrollment.objects.filter(
                madrassa_class_id=class_id, status=Enrollment.Status.ENROLLED
            ).values_list("student_id", flat=True)
        )
        for student_id in student_ids:
            Attendance.objects.update_or_create(
                student_id=student_id,
                date=date_obj,
                defaults={"status": Attendance.Status.PRESENT, "madrassa_class_id": class_id},
            )
        return HttpResponse(
            "",
            status=204,
            headers={"HX-Trigger": '"attendanceChanged"'},
        )


class FeeListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = Fee
    template_name = "madrassa/fee_list.html"
    partial_template = "madrassa/partials/fee_list_content.html"

    def get_queryset(self):
        return Fee.objects.select_related("madrassa_class").order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_fees"] = self.object_list.filter(is_active=True).count()
        ctx["fee_count"] = self.object_list.count()
        return ctx


class FeeCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = Fee
    form_class = FeeForm
    template_name = "madrassa/fee_form.html"
    success_url = reverse_lazy("madrassa:fees")

    def get_modal_title(self):
        return "Add fee"


class FeeUpdateView(LoginRequiredMixin, HTMXModalFormMixin, UpdateView):
    model = Fee
    form_class = FeeForm
    template_name = "madrassa/fee_form.html"
    success_url = reverse_lazy("madrassa:fees")

    def get_modal_title(self):
        return f"Edit {self.object.name}"


class FeeDeleteView(LoginRequiredMixin, HTMXDeleteMixin, DeleteView):
    model = Fee
    success_url = reverse_lazy("madrassa:fees")


class FeePaymentListView(LoginRequiredMixin, HTMXPartialMixin, ListView):
    model = FeePayment
    template_name = "madrassa/payment_list.html"
    partial_template = "madrassa/partials/payment_list_content.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = FeePayment.objects.select_related("student", "fee", "fund").order_by("-date", "-id")
        q = self.request.GET.get("q", "").strip()
        method = self.request.GET.get("method", "").strip()
        date_from = self.request.GET.get("date_from", "").strip()
        date_to = self.request.GET.get("date_to", "").strip()
        if q:
            queryset = queryset.filter(
                Q(student__full_name__icontains=q)
                | Q(receipt_number__icontains=q)
                | Q(fee__name__icontains=q)
            )
        if method:
            queryset = queryset.filter(method=method)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["selected_method"] = self.request.GET.get("method", "")
        ctx["date_from"] = self.request.GET.get("date_from", "")
        ctx["date_to"] = self.request.GET.get("date_to", "")
        ctx["filtered_total"] = money(self.object_list.aggregate(s=Sum("amount"))["s"])
        ctx["total_collected"] = money(FeePayment.objects.aggregate(s=Sum("amount"))["s"])
        today = date.today()
        ctx["month_collected"] = money(
            FeePayment.objects.filter(date__year=today.year, date__month=today.month).aggregate(
                s=Sum("amount")
            )["s"]
        )
        ctx["payment_count"] = FeePayment.objects.count()
        return ctx


class FeePaymentCreateView(LoginRequiredMixin, HTMXModalFormMixin, CreateView):
    model = FeePayment
    form_class = FeePaymentForm
    template_name = "madrassa/payment_form.html"
    success_url = reverse_lazy("madrassa:payments")

    def get_modal_title(self):
        return "Record fee payment"
