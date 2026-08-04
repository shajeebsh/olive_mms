from datetime import date

from django.db import models

from core.models import TimeStampedModel


class Class(TimeStampedModel):
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=50, blank=True)
    teacher = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes_taught",
    )
    schedule = models.CharField(max_length=150, blank=True)
    capacity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "classes"

    def __str__(self):
        return self.name


class Student(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        SUSPENDED = "SUSPENDED", "Suspended"
        GRADUATED = "GRADUATED", "Graduated"

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    family = models.ForeignKey(
        "members.Family",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    guardian = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=30, blank=True)
    admission_date = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class Enrollment(TimeStampedModel):
    class Status(models.TextChoices):
        ENROLLED = "ENROLLED", "Enrolled"
        COMPLETED = "COMPLETED", "Completed"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    madrassa_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="enrollments")
    academic_year = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENROLLED)

    class Meta:
        ordering = ["-academic_year", "student__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "madrassa_class", "academic_year"],
                name="unique_enrollment_per_year",
            )
        ]

    def __str__(self):
        return f"{self.student} → {self.madrassa_class} ({self.academic_year})"


class Attendance(TimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records")
    madrassa_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
    )
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date", "student__full_name"]
        verbose_name_plural = "attendance records"
        constraints = [
            models.UniqueConstraint(fields=["student", "date"], name="unique_attendance_per_student_day")
        ]

    def __str__(self):
        return f"{self.student} {self.get_status_display()} on {self.date}"


class Fee(TimeStampedModel):
    class Frequency(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        TERM = "TERM", "Per term"
        ANNUAL = "ANNUAL", "Annual"

    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY)
    madrassa_class = models.ForeignKey(
        Class,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fees",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FeePayment(TimeStampedModel):
    class Method(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        BANK = "BANK", "Bank transfer"
        ONLINE = "ONLINE", "Online"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_payments")
    fee = models.ForeignKey(Fee, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    fund = models.ForeignKey(
        "finance.Fund",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fee_payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=date.today)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    receipt_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.student} {self.amount} on {self.date}"

    def save(self, *args, **kwargs):
        if self.amount is None and self.fee_id:
            self.amount = self.fee.amount
        if not self.receipt_number:
            daily_count = FeePayment.objects.filter(date=self.date).count() + 1
            self.receipt_number = f"PAY-{self.date:%Y%m%d}-{daily_count:04d}"
        super().save(*args, **kwargs)
