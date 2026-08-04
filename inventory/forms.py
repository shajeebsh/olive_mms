from django import forms

from .models import Category, Item, StockLevel, StockMovement


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget_class = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", widget_class)


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class ItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Item
        fields = ["name", "category", "unit", "price", "low_stock_threshold", "is_active"]
        widgets = {
            "category": forms.Select(),
            "price": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "low_stock_threshold": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        self.fields["category"].queryset = Category.objects.order_by("name")


class StockMovementForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = [
            "item",
            "movement_type",
            "qty_change",
            "date",
            "purpose",
            "event",
            "recipient",
            "recipient_name",
            "notes",
        ]
        widgets = {
            "item": forms.Select(),
            "movement_type": forms.Select(),
            "qty_change": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "event": forms.Select(),
            "recipient": forms.Select(),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["item"].queryset = Item.objects.filter(is_active=True).order_by("name")
        self.fields["event"].queryset = self.fields["event"].queryset.order_by("-date_from")
        self.fields["event"].required = False
        self.fields["recipient"].queryset = self.fields["recipient"].queryset.order_by("full_name")
        self.fields["recipient"].required = False
        self.fields["recipient_name"].required = False
        self.fields["purpose"].required = False

    def clean(self):
        cleaned = super().clean()
        movement_type = cleaned.get("movement_type")
        qty = cleaned.get("qty_change")
        if qty is not None and qty <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")

        if movement_type == StockMovement.MovementType.OUT:
            recipient = cleaned.get("recipient")
            recipient_name = (cleaned.get("recipient_name") or "").strip()
            if not recipient and not recipient_name:
                raise forms.ValidationError(
                    "Add a recipient (member) or a recipient name for a distribution."
                )
            item = cleaned.get("item")
            if item:
                available = StockLevel.objects.filter(item=item).values_list(
                    "quantity", flat=True
                ).first() or 0
                if qty is not None and qty > available:
                    raise forms.ValidationError(
                        f"Not enough stock — only {available} available for {item.name}."
                    )
        return cleaned


class DistributionForm(StockMovementForm):
    """Stock movement pre-set to OUT for the distribution workflow."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("movement_type")

    def clean(self):
        self.cleaned_data["movement_type"] = StockMovement.MovementType.OUT
        return super().clean()
