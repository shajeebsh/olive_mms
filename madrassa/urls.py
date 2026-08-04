from django.urls import path

from . import views

app_name = "madrassa"

urlpatterns = [
    path("", views.MadrassaDashboardView.as_view(), name="index"),
    path("classes/", views.ClassListView.as_view(), name="classes"),
    path("classes/new/", views.ClassCreateView.as_view(), name="class_create"),
    path("classes/<int:pk>/edit/", views.ClassUpdateView.as_view(), name="class_update"),
    path("classes/<int:pk>/delete/", views.ClassDeleteView.as_view(), name="class_delete"),
    path("students/", views.StudentListView.as_view(), name="students"),
    path("students/<int:pk>/", views.StudentDetailView.as_view(), name="student_detail"),
    path("students/new/", views.StudentCreateView.as_view(), name="student_create"),
    path("students/<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student_update"),
    path("students/<int:pk>/delete/", views.StudentDeleteView.as_view(), name="student_delete"),
    path("enrollments/", views.EnrollmentListView.as_view(), name="enrollments"),
    path("enrollments/new/", views.EnrollmentCreateView.as_view(), name="enrollment_create"),
    path("enrollments/<int:pk>/edit/", views.EnrollmentUpdateView.as_view(), name="enrollment_update"),
    path("enrollments/<int:pk>/delete/", views.EnrollmentDeleteView.as_view(), name="enrollment_delete"),
    path("attendance/", views.AttendanceListView.as_view(), name="attendance"),
    path("attendance/set/", views.AttendanceSetView.as_view(), name="attendance_set"),
    path("attendance/mark-all/", views.AttendanceMarkAllView.as_view(), name="attendance_mark_all"),
    path("fees/", views.FeeListView.as_view(), name="fees"),
    path("fees/new/", views.FeeCreateView.as_view(), name="fee_create"),
    path("fees/<int:pk>/edit/", views.FeeUpdateView.as_view(), name="fee_update"),
    path("fees/<int:pk>/delete/", views.FeeDeleteView.as_view(), name="fee_delete"),
    path("payments/", views.FeePaymentListView.as_view(), name="payments"),
    path("payments/new/", views.FeePaymentCreateView.as_view(), name="payment_create"),
]
