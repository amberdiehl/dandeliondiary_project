import re
from django import forms
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from compare.helpers import get_month_options
from helpers import validate_expense_note_input, helper_budget_categories
from models import MyNoteTag, MyQuickAddCategoryAssociation


RE_VALID_CHOICE_VALUE = re.compile(r'^[\d]*$')
RE_VALID_CHOICE_PLACE = re.compile(r'^[\w\' .&-^]*$')
RE_VALID_PAYEE_CONTAINS = re.compile(r'^[\w\d ,.\-()*&]{0,80}$')


def validate_option_value(value):
    if not re.match(RE_VALID_CHOICE_VALUE, value):
        raise ValidationError('Malformed option.')


def validate_place_value(value):
    if not re.match(RE_VALID_CHOICE_PLACE, value):
        raise ValidationError('Malformed place value provided.')


class CategoryCustomChoiceField(forms.ChoiceField):
    def validate(self, value):
        pass
        # if int(value) == 0:
        #    raise validators.ValidationError(u'Select a budget category.')
        # With two potential choices, validation must happen at the form level


class NewExpenseForm(forms.Form):

    amount_receipt = forms.DecimalField(
        label=_("Receipt total:"),
        max_digits=11,
        decimal_places=2,
        min_value=0.01,
        max_value=999999999.99,
        widget=forms.NumberInput(attrs={'placeholder': '0.00'}),
        required=True,
        help_text=_("Amount total as shown on receipt.")
    )
    amount = forms.DecimalField(
        label=_("Amount:"),
        max_digits=11,
        decimal_places=2,
        min_value=0,
        max_value=999999999.99,
        widget=forms.NumberInput(attrs={'placeholder': '0.00'}),
        required=False,
        help_text=_("Purchase amount; leave empty if same as receipt total.")
    )
    note = forms.CharField(
        label=_("Note:"),
        max_length=512,
        widget=forms.TextInput(attrs={'placeholder': 'Optional brief purchase note.'}),
        required=False,
        help_text=_("Optional brief note to remember something about this purchase.")
    )
    choose_place = CategoryCustomChoiceField(
        validators=[validate_place_value],
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
    split = forms.BooleanField(
        label=_("Split?"),
        required=False
    )
    amount_split = forms.DecimalField(
        label=_("Split amount:"),
        max_digits=11,
        decimal_places=2,
        min_value=0,
        max_value=999999999.99,
        widget=forms.NumberInput(attrs={'placeholder': '0.00'}),
        required=False,
        help_text=_("Split amount from total purchase.")
    )
    note_split = forms.CharField(
        label=_("Split note:"),
        max_length=512,
        widget=forms.TextInput(attrs={'placeholder': 'Optional brief purchase note.'}),
        required=False,
        help_text=_("Optional brief note to remember something about this purchase.")
    )
    choose_category_split = CategoryCustomChoiceField(
        validators=[validate_option_value],
        label=_("Split category:"),
        help_text=_("Apply this amount to this category.")
    )
    hidden_places = forms.CharField(
        widget=forms.HiddenInput,
        required=False,
    )
    hidden_categories = forms.CharField(
        widget=forms.HiddenInput,
        required=False,
    )

    def clean_choose_place(self):
        place = self.cleaned_data['choose_place']
        return place

    def clean_choose_category(self):
        category = self.cleaned_data['choose_category']
        if category == '0':
            error = 'Please select a budget category.'
            raise forms.ValidationError(_(error))
        return category

    def clean_note(self):
        note = self.cleaned_data['note']
        if not validate_expense_note_input(note):
            error = 'Special characters in your note must be limited to: . , () + - and =.'
            raise forms.ValidationError(_(error))
        return note

    def clean_note_split(self):
        note = self.cleaned_data['note_split']
        if not validate_expense_note_input(note):
            error = 'Special characters in your note must be limited to: . , () + - and =.'
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

        selected_place = self.cleaned_data['choose_place']
        if not selected_place == '0' and not selected_place == '':
            category = self.cleaned_data.get('choose_category', None)
            if category:
                place_categories = self.cleaned_data.get('hidden_categories', '')
                if category not in place_categories:
                    self.add_error('choose_category', "Select a category associated with the place you have selected.")

        if self.cleaned_data['split']:

            split_amount = self.cleaned_data['amount_split']
            if not split_amount:
                self.add_error('amount_split', "With split selected, you must enter an amount to split.")

            split_category = int(self.cleaned_data['choose_category_split'])
            if split_category == 0:
                self.add_error('choose_category_split', 'With split selected, you must choose a split category.')

        return self.cleaned_data


class MyNoteTagForm(forms.ModelForm):

    class Meta:
        model = MyNoteTag
        fields = ['tag', 'is_default', ]
        widgets = {
            'tag': forms.TextInput(attrs={'placeholder': 'Note tag'}),
        }

    def clean_tag(self):
        new_tag = self.cleaned_data['tag']
        # Validate use of special characters
        if not validate_expense_note_input(new_tag):
            error = 'Limited special characters to: . , ( ) + - ='
            raise forms.ValidationError(_(error))
        return new_tag


class MyQuickAddCategoryAssociationForm(forms.ModelForm):

    class Meta:
        model = MyQuickAddCategoryAssociation
        fields = ['payee_contains', 'category', ]
        widgets = {
            'payee_contains': forms.TextInput(attrs={'placeholder': 'Partial description to match'}),
        }

    def __init__(self, household=0, *args, **kwargs):
        super(MyQuickAddCategoryAssociationForm, self).__init__(*args, **kwargs)
        category_choices = helper_budget_categories(household, top_load=True)
        self.fields['category'].choices = category_choices

    def clean_payee_contains(self):
        payee_contains = self.cleaned_data['payee_contains']
        # Validate use of special characters
        if not re.match(RE_VALID_PAYEE_CONTAINS, payee_contains):
            error = 'Limited special characters to: . , ( ) + - ='
            raise forms.ValidationError(_(error))
        return payee_contains


class UploadFileForm(forms.Form):
    file = forms.FileField(
        label=_("CSV file:"),
        widget=forms.FileInput(),
        required=True,
    )
    period = forms.ChoiceField(
        choices=get_month_options(),
        required=True,
    )
    date_format = forms.ChoiceField(
        choices=[('%m-%d-%Y', 'm-d-y'), ('%Y-%m-%d', 'y-m-d')],
        required=True,
    )
