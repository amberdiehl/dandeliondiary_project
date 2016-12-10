from django import forms
from django.utils.translation import ugettext_lazy as _


class CategoryCustomChoiceField(forms.ChoiceField):
    def validate(self, value):
        pass
        # if int(value) == 0:
        #    raise validators.ValidationError(u'Select a budget category.')
        # With two potential choices, validation must happen at the form level


class NewExpenseForm(forms.Form):

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
    choose_category_place = CategoryCustomChoiceField(
        label=_("Budget place category:"),
        help_text=_("Apply this purchase to a budget category.")
    )
    choose_place = CategoryCustomChoiceField(
        label=_("Place"),
        help_text=_("Purchase made at this location.")
    )
    choose_category = CategoryCustomChoiceField(
        label=_("Budget category:"),
        help_text=_("Apply this purchase to a budget category.")
    )
    expense_date = forms.DateField(
        label=_("Date:"),
        widget=forms.DateInput,
        required=False,
        help_text=_("Defaults to today; otherwise, select date to apply to budget.")
    )

    def clean(self):
        value1 = int(self.cleaned_data['choose_category_place'])
        value2 = int(self.cleaned_data['choose_category'])
        if value1 == 0 and value2 == 0:
            self.add_error('choose_category', "Select a budget category.")
            self.add_error('choose_category_place', "Select a budget category.")
