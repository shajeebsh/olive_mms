from django import forms

from .models import Donation, DonationType, Pledge


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", widget_class)


class DonationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Donation
        fields = [
            "member",
            "donation_type",
            "fund",
            "amount",
            "payment_method",
            "date",
            "reference_no",
            "notes",
        ]
        widgets = {
            "member": forms.Select(),
            "donation_type": forms.Select(),
            "fund": forms.Select(),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "payment_method": forms.Select(),
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class PledgeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Pledge
        fields = [
            "member",
            "donation_type",
            "amount",
            "start_date",
            "end_date",
            "frequency",
            "is_active",
            "notes",
        ]
        widgets = {
            "member": forms.Select(),
            "donation_type": forms.Select(),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "frequency": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class DonationTypeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = DonationType
        fields = ["code", "name", "is_active", "default_account_hint"]
