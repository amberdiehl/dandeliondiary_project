import re
from django import forms
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from helpers import validate_expense_note_input


RE_VALID_CHOICE_VALUE = re.compile(r'^[\d]*$')


def validate_option_value(value):
    if not re.match(RE_VALID_CHOICE_VALUE, value):
        raise ValidationError('Malformed option.')


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
        validators=[validate_option_value],
        label=_("Budget place category:"),
        help_text=_("Apply this purchase to a budget category.")
    )
    choose_place = CategoryCustomChoiceField(
        validators=[validate_option_value],
        label=_("Place"),
        help_text=_("Purchase made at this location.")
    )
    choose_category = CategoryCustomChoiceField(
        validators=[validate_option_value],
        label=_("Budget category:"),
        help_text=_("Apply this purchase to a budget category.")
    )
    expense_date = forms.DateField(
        label=_("Date:"),
        widget=forms.DateInput,
        required=False,
        help_text=_("Defaults to today; otherwise, select date to apply to budget.")
    )
    receipt = forms.ImageField(
        label=_("Receipt (optional):"),
        required=False,
        help_text=_("Capture your receipt for your records.")
    )

    def clean_note(self):
        note = self.cleaned_data['note']
        if not validate_expense_note_input(note):
            error = 'Special characters in your note must be limited to: . , () + - / and =.'
            raise forms.ValidationError(_(error))
        return note


    def clean_receipt(self):
        receipt = self.cleaned_data['receipt']
        if receipt:
            content_type = receipt.content_type.split('/')[0]
            if content_type in settings.CONTENT_TYPES:
                if receipt.size > settings.MAX_UPLOAD_SIZE:
                    error = 'Please keep file size under {}; current file size is {}.'\
                        .format(filesizeformat(settings.MAX_UPLOAD_SIZE), filesizeformat(receipt.size))
                    raise forms.ValidationError(_(error))
            else:
                raise forms.ValidationError(_('File type is not supported.'))

        return receipt

    def clean(self):
        value1 = int(self.cleaned_data['choose_category_place'])
        value2 = int(self.cleaned_data['choose_category'])

        # A place based or non-place based expense category must be selected, but not both
        if value1 == 0 and value2 == 0:
            self.add_error('choose_category', "Select a budget category.")
            self.add_error('choose_category_place', "Select a budget category.")

        if value1 and value2:
            self.add_error('choose_category', "Make only one budget category selection.")
            self.add_error('choose_category_place', "Make only one budget category selection.")

        # If place based selection is made, place must also be selected
        try:
            value3 = int(self.cleaned_data['choose_place'])
        except ValueError:
            if value1 == 0:
                self.add_error('choose_category_place', 'Select a place based expense category.')
        else:
            if value1 != 0:
                self.add_error('choose_place', 'You selected an expense category based on place; '
                                               'select place.')

        return self.cleaned_data
