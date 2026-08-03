from django import forms

from .models import MosqueProfile


class MosqueProfileForm(forms.ModelForm):
    class Meta:
        model = MosqueProfile
        fields = [
            "name",
            "tagline",
            "address",
            "city",
            "phone",
            "email",
            "bank_name",
            "bank_account",
            "bank_iban",
            "hijri_offset",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "tagline": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "bank_account": forms.TextInput(attrs={"class": "form-control"}),
            "bank_iban": forms.TextInput(attrs={"class": "form-control"}),
            "hijri_offset": forms.NumberInput(attrs={"class": "form-control"}),
        }
