from django import forms

from .models import Attendance, Class, Enrollment, Fee, FeePayment, Student


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", widget_class)


class ClassForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Class
        fields = ["name", "level", "teacher", "schedule", "capacity", "is_active"]
        widgets = {
            "teacher": forms.Select(),
            "capacity": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher"].queryset = self.fields["teacher"].queryset.order_by("full_name")
        self.fields["capacity"].required = False

    def clean_capacity(self):
        return self.cleaned_data.get("capacity") or 0


class StudentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "full_name",
            "member",
            "family",
            "date_of_birth",
            "guardian",
            "guardian_phone",
            "admission_date",
            "status",
            "notes",
        ]
        widgets = {
            "member": forms.Select(),
            "family": forms.Select(),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "admission_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = self.fields["member"].queryset.order_by("full_name")
        self.fields["family"].queryset = self.fields["family"].queryset.order_by("name")


class EnrollmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "madrassa_class", "academic_year", "status"]
        widgets = {
            "student": forms.Select(),
            "madrassa_class": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.filter(
            status=Student.Status.ACTIVE
        ).order_by("full_name")
        self.fields["madrassa_class"].queryset = Class.objects.filter(is_active=True).order_by("name")


class FeeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Fee
        fields = ["name", "amount", "frequency", "madrassa_class", "is_active"]
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "madrassa_class": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["madrassa_class"].queryset = Class.objects.filter(is_active=True).order_by("name")
        self.fields["madrassa_class"].required = False


class FeePaymentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ["student", "fee", "fund", "amount", "date", "method", "notes"]
        widgets = {
            "student": forms.Select(),
            "fee": forms.Select(),
            "fund": forms.Select(),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = Student.objects.filter(
            status=Student.Status.ACTIVE
        ).order_by("full_name")
        self.fields["fee"].queryset = Fee.objects.filter(is_active=True).order_by("name")
        self.fields["fee"].required = False
        self.fields["amount"].required = False
        self.fields["fund"].queryset = self.fields["fund"].queryset.order_by("name")
        self.fields["fund"].required = False

    def clean(self):
        cleaned = super().clean()
        fee = cleaned.get("fee")
        amount = cleaned.get("amount")
        if fee and amount is None:
            cleaned["amount"] = fee.amount
        elif fee is None and amount is None:
            raise forms.ValidationError("Enter an amount or pick a fee to use its default.")
        return cleaned
