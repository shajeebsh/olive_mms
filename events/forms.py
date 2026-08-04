from django import forms

from .models import Event, EventAttendance


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", widget_class)


class EventForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = ["name", "event_type", "date_from", "date_to", "location", "budget", "status", "notes"]
        widgets = {
            "event_type": forms.Select(),
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
            "budget": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "status": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        if date_from and date_to and date_to < date_from:
            raise forms.ValidationError("End date cannot be before the start date.")
        return cleaned


class EventAttendanceForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = EventAttendance
        fields = ["event", "member", "role"]
        widgets = {
            "event": forms.Select(),
            "member": forms.Select(),
            "role": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = self.fields["member"].queryset.order_by("full_name")
