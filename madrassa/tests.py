from datetime import date
from decimal import Decimal

from django.test import TestCase

from finance.models import Fund, Income
from members.models import Family, Member

from .models import Attendance, Class, Enrollment, Fee, FeePayment, Student


class MadrassaSignalTests(TestCase):
    def setUp(self):
        self.fund = Fund.objects.create(name="Education", code="EDU")
        self.student = Student.objects.create(full_name="Fatima Zahra")
        self.fee = Fee.objects.create(name="Monthly tuition", amount="50.00")

    def test_fee_payment_posts_income_to_fund(self):
        payment = FeePayment.objects.create(
            student=self.student, fee=self.fee, amount=Decimal("50.00"), fund=self.fund
        )
        income = Income.objects.get(fee_payment=payment)
        self.assertEqual(income.amount, Decimal("50.00"))
        self.assertEqual(income.fund, self.fund)
        self.assertEqual(income.source, "Madrassa fee")

    def test_fee_payment_defaults_to_edu_fund(self):
        payment = FeePayment.objects.create(student=self.student, fee=self.fee, amount=Decimal("50.00"))
        income = Income.objects.get(fee_payment=payment)
        self.assertEqual(income.fund.code, "EDU")

    def test_fee_payment_amount_defaults_to_fee(self):
        payment = FeePayment.objects.create(student=self.student, fee=self.fee, fund=self.fund)
        self.assertEqual(payment.amount, self.fee.amount)

    def test_fee_payment_receipt_number_generated(self):
        payment = FeePayment.objects.create(
            student=self.student, fee=self.fee, amount=Decimal("50.00")
        )
        self.assertTrue(payment.receipt_number.startswith("PAY-"))

    def test_fee_payment_delete_removes_income(self):
        payment = FeePayment.objects.create(
            student=self.student, fee=self.fee, amount=Decimal("50.00"), fund=self.fund
        )
        payment.delete()
        self.assertFalse(Income.objects.filter(fee_payment_id=payment.pk).exists())


class MadrassaModelTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(full_name="Yusuf", guardian="Ahmad")
        self.madrassa_class = Class.objects.create(name="Quran Level 1")
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            madrassa_class=self.madrassa_class,
            academic_year="2026",
        )

    def test_enrollment_unique_per_year(self):
        with self.assertRaises(Exception):
            Enrollment.objects.create(
                student=self.student,
                madrassa_class=self.madrassa_class,
                academic_year="2026",
            )

    def test_attendance_unique_per_student_day(self):
        day = date(2026, 8, 4)
        Attendance.objects.create(student=self.student, madrassa_class=self.madrassa_class, date=day)
        with self.assertRaises(Exception):
            Attendance.objects.create(student=self.student, date=day)
