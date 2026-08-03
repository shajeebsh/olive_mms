from django import forms

from .models import Expense, Fund, FundTransfer, Income


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ["name", "code", "opening_balance", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "opening_balance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["fund", "date", "amount", "category", "description", "payee"]
        widgets = {
            "fund": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
            "payee": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fund"].queryset = Fund.objects.filter(is_active=True)


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ["fund", "date", "amount", "source", "description"]
        widgets = {
            "fund": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "source": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fund"].queryset = Fund.objects.filter(is_active=True)
        self.fields["source"].required = True


class FundTransferForm(forms.ModelForm):
    class Meta:
        model = FundTransfer
        fields = ["from_fund", "to_fund", "amount", "date", "note"]
        widgets = {
            "from_fund": forms.Select(attrs={"class": "form-select"}),
            "to_fund": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "note": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["from_fund"].queryset = Fund.objects.filter(is_active=True)
        self.fields["to_fund"].queryset = Fund.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        from_fund = cleaned.get("from_fund")
        to_fund = cleaned.get("to_fund")
        if from_fund and to_fund and from_fund.pk == to_fund.pk:
            raise forms.ValidationError("Source and destination funds must be different.")
        return cleaned
