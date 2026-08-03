from django import forms

from .models import Family, Member


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", widget_class)


class MemberForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            "family",
            "full_name",
            "date_of_birth",
            "phone",
            "email",
            "join_date",
            "membership_status",
            "member_role",
            "notes",
        ]
        widgets = {
            "family": forms.Select(),
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            "join_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class FamilyForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Family
        fields = ["name", "head", "address", "phone", "email", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
