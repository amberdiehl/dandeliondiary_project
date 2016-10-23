from django import forms
from django.core import validators
from django.utils.translation import ugettext_lazy as _


class CategoryCustomChoiceField(forms.ChoiceField):
    def validate(self, value):
        if int(value) == 0:
            raise validators.ValidationError(u'Select a budget category.')


class NewExpenseForm(forms.Form):

    choose_place = forms.ChoiceField(
        label='Found nearby places:',
        required=False
    )

    amount = forms.DecimalField(
        label=_("Amount:"),
        max_digits=11,
        decimal_places=2,
        min_value=1,
        max_value=999999999.99,
        widget=forms.NumberInput(attrs={'placeholder': '0.00'}),
        required=True,
        help_text=_("Purchase amount.")
    )
    note = forms.CharField(
        label=_("Note:"),
        max_length=512,
        widget=forms.TextInput(attrs={'placeholder': 'Optional brief purchase note.'}),
        required=False,
        help_text=_("Optional brief note to remember something about this purchase.")
    )
    choose_category = CategoryCustomChoiceField(
        label=_("Budget category:"),
        help_text=_("Apply this purchase to a budget category.")
    )
    expense_date = forms.DateField(
        label=("Date:"),
        widget=forms.DateInput,
        required=False,
        help_text=_("Defaults to today; otherwise, select date to apply to budget.")
    )
