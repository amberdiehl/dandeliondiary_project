from django import forms
from django.utils.translation import ugettext_lazy as _
from models import RVHousehold, Vehicle
from helpers import *
import re

from account.models import EmailAddress

from .models import HouseholdInvite


re_validate_names = re.compile(r"^[A-Za-z\-]*$")
re_formatted_phone = re.compile(r"^\d\d\d-\d\d\d-\d\d\d\d$")
re_phone = re.compile(r"^\d\d\d\d\d\d\d\d\d\d$")
re_same3 = re.compile(r"^1{3}|2{3}|3{3}|4{3}|5{3}|6{3}|7{3}|8{3}|9{3}|0{3}$")
re_same4 = re.compile(r"^1{4}|2{4}|3{4}|4{4}|5{4}|6{4}|7{4}|8{4}|9{4}|0{4}$")


class MyInfoForm(forms.Form):
    # First + last name to update native Django user.
    first_name = forms.CharField(
        label=_("First name:"),
        max_length=30,
        min_length=2,
        widget=forms.TextInput(attrs={'placeholder': 'First name'}),
        required=True,
        help_text=_("Your first name or nickname.")
    )
    last_name = forms.CharField(
        label=_("Last name: "),
        max_length=30,
        min_length=2,
        widget=forms.TextInput(attrs={'placeholder': 'Last name'}),
        required=True,
        help_text=_("Your last name.")
    )

    # Household member data
    phone_number = forms.CharField(
        label=_("Phone number: "),
        max_length=12,
        widget=forms.TextInput(attrs={'placeholder': '555-555-5555'}),
        required=True,
        help_text=_("Your phone number; preferably, cell.")
    )
    owner = forms.BooleanField(
        label=_("Household owner: "),
        widget=forms.CheckboxInput(attrs={'disabled': True}),
        required=False,
        help_text=_("Household member owner status.")
    )

    def __init__(self, *args, **kwargs):
        super(MyInfoForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['first_name', 'last_name', 'phone_number', 'owner']

    def clean_first_name(self):
        data = self.cleaned_data['first_name']
        if re_validate_names.search(data):
            pass
        else:
            raise forms.ValidationError("Name can only contain letters and hyphens.")
        return data

    def clean_last_name(self):
        data = self.cleaned_data['last_name']
        if re_validate_names.search(data):
            pass
        else:
            raise forms.ValidationError("Name can only contain letters and hyphens.")
        return data

    def clean_phone_number(self):
        data = self.cleaned_data['phone_number']

        area = re_same3.search(data[0:3])
        exchange = re_same3.search(data[3:6])
        line = re_same4.search(data[6:10])

        if area or (area and exchange) or (area and line) or (exchange and line) or (area and exchange and line):
            # dummy phone number with a lot of repeating digits; e.g. 111-111-1111, 111-222-3333
            raise forms.ValidationError("Please enter a valid phone number.")
        else:
            if len(data) < 10:
                raise forms.ValidationError("Please be sure to include area code.")
            else:
                if re_phone.search(data):
                    data = data[0:3] + "-" + data[3:6] + "-" + data[6:10]
                else:
                    if re_formatted_phone.search(data):
                        pass
                    else:
                        # too many digits
                        raise forms.ValidationError("Please enter a valid phone number.")
        return data


class HouseholdProfileForm(forms.ModelForm):

    class Meta:
        model = RVHousehold
        fields = ['start_year', 'members_in_household', 'oldest_birthyear', 'rig_type', 'use_type', 'income_type',
                  'pets_dog', 'pets_cat', 'pets_other',
                  'children', 'children_status', 'grandchildren' ,'grandchildren_status']
        exclude = ['paid_through', 'budget_model', 'subscription_status']
        labels = {
            'members_in_household': _('Adults in household'),
            'oldest_birthyear': _('Oldest birth year'),
            'pets_dog': _('Number of dogs'),
            'pets_cat': _('Number of cats'),
            'pets_other': _('Number of other pets'),
            'children': _('Number of children'),
            'grandchildren': _('Number of grandchildren')
        }
        widgets = {
            'start_year': forms.TextInput(attrs={'placeholder': datetime.datetime.now().year}),
            'members_in_household': forms.TextInput(attrs={'placeholder': 'e.g. 2'}),
            'oldest_birthyear': forms.TextInput(attrs={'placeholder': 'e.g. ' + str(datetime.datetime.now().year - 60)}),
            'pets_dog': forms.TextInput(attrs={'placeholder': 'Number of dogs'}),
            'pets_cat': forms.TextInput(attrs={'placeholder': 'Number of cats'}),
            'pets_other': forms.TextInput(attrs={'placeholder': 'Number of other pets'}),
            'children': forms.TextInput(attrs={'placeholder': 'Number of children you have'}),
            'grandchildren': forms.TextInput(attrs={'placeholder': 'Number of grandchildren you have'}),
        }
        help_texts = {
            'start_year': _('Year you first owned an RV.'),
            'members_in_household': _('Total number of adults in your household.'),
            'oldest_birthyear': _('The birth date year of the oldest person in your household.'),
            'rig_type': _('Type of RV.'),
            'use_type': _('How you use your RV.'),
            'income_type': _('Primary source of income for your household.'),
            'pets_dog': _('Number of dogs in your household; if none, 0.'),
            'pets_cat': _('Number of cats in your household; if none, 0.'),
            'pets_other': _('Number of pets other than dogs or cats in your household; if none, 0.'),
            'children': _('Number of children you have.'),
            'children_status': _('Status of your children in relation to your household.'),
            'grandchildren': _('Number of grandchldren you have.'),
            'grandchildren_status': _('Status of your grandchildren in relation to your household.'),
        }

    def clean_start_year(self):
        data = self.cleaned_data.get('start_year')
        if data > datetime.datetime.now().year or data < datetime.datetime.now().year - 65:
            self.add_error('start_year', 'Start year not valid.')
        return data

    def clean_members_in_household(self):
        data = self.cleaned_data.get('members_in_household')
        if data > 10 or data < 1:
            self.add_error('members_in_household',
                           'There must be at least 1 member in a household and no more than 10.')
        return data

    def clean_oldest_birthyear(self):
        data = self.cleaned_data.get('oldest_birthyear')
        if data > datetime.datetime.now().year - 18 or data < datetime.datetime.now().year - 85:
            self.add_error('oldest_birthyear',
                       'An invalid birth date year was provided.')
        return data

    def clean_rig_type(self):
        data = self.cleaned_data.get('rig_type')
        if data == 0:
            self.add_error('rig_type', 'Please select type of rig.')
        return data

    def clean_use_type(self):
        data = self.cleaned_data.get('use_type')
        if data == 0:
            self.add_error('use_type', 'Please indicate how you use your RV.')
        return data

    def clean_income_type(self):
        data = self.cleaned_data.get('income_type')
        if data == 0:
            self.add_error('income_type', 'Please specify primary source of income for your household.')
        return data

    def clean_pets_dog(self):
        data = self.cleaned_data.get('pets_dog')
        if data > 10:
            self.add_error('pets_dog', 'No more than 10 dogs may be specified.')
        if data < 0:
            self.add_error('pets_dog', 'Cannot specify less than 0 pets.')
        return data

    def clean_pets_cat(self):
        data = self.cleaned_data.get('pets_cat')
        if data > 10:
            self.add_error('pets_cat', 'No more than 10 cats may be specified.')
        if data < 0:
            self.add_error('pets_cat', 'Cannot specify less than 0 pets.')
        return data

    def clean_pets_other(self):
        data = self.cleaned_data.get('pets_other')
        if data > 10:
            self.add_error('pets_other', 'No more than 10 pets besides dogs and cats may be specified.')
        if data < 0:
            self.add_error('pets_other', 'Cannot specify less than 0 pets.')
        return data

    def clean_children(self):
        data = self.cleaned_data.get('children')
        if data > 20:
            self.add_error('children', 'Cannot specify more than 20 children.')
        if data < 0:
            self.add_error('children', 'Cannot specify less than 0 children.')
        return data

    def clean_grandchildren(self):
        data = self.cleaned_data.get('grandchildren')
        if data > 100:
            self.add_error('grandchildren', 'Cannot specify more than 100 grandchildren.')
        if data < 0:
            self.add_error('grandchildren', 'Cannot specify less than 0 grandchildren.')
        return data

    def clean(self):
        if 'children' in self.cleaned_data:
            if (self.cleaned_data['children'] > 0) and (int(self.cleaned_data['children_status']) == 0):
                self.add_error('children_status', "Please indicate if your children visit or live with you.")

            if (self.cleaned_data['children'] == 0) and (int(self.cleaned_data['children_status']) > 0):
                self.add_error('children', "Please specify how many children you have.")

        if 'grandchildren' in self.cleaned_data:
            if (self.cleaned_data['grandchildren'] > 0) and (int(self.cleaned_data['grandchildren_status']) == 0):
                self.add_error('grandchildren_status', "Please indicate if your grandchildren visit or live with you.")

            if (self.cleaned_data['grandchildren'] == 0) and (int(self.cleaned_data['grandchildren_status']) > 0):
                self.add_error('grandchildren', "Please specify how many grandchildren you have.")


class InviteMemberForm(forms.Form):
    email = forms.EmailField(
        label=_("Email address:"),
        max_length=254,
        widget=forms.TextInput(attrs={'placeholder': "Member's email address"}),
        required=True,
        help_text=_("Send invitation for household member to this address.")
    )

    def clean_email(self):
        data = self.cleaned_data['email']
        qs1 = EmailAddress.objects.filter(email__iexact=data).values()
        if len(qs1) == 0:
            # Note: email must be unique across ANY invite and household
            qs2 = HouseholdInvite.objects.filter(email__iexact=data).values()
            if len(qs2) == 0:
                pass
            else:
                raise forms.ValidationError("An invite is pending to this email address.")
        else:
            raise forms.ValidationError("Cannot send an invite to this email address.")
        return data


class VehicleForm(forms.ModelForm):

    class Meta:
        model = Vehicle
        fields = ['type', 'make', 'model_name', 'model_year', 'fuel', 'purchase_year', 'purchase_price',
                  'purchase_type', 'finance', 'satisfaction', 'status', 'gone_year']
        widgets = {
            'type': forms.Select(attrs={'onchange': 'FilterMakes(event);'}),
            'make': forms.Select(attrs={'onchange': 'FilterModels(event);'}),
            'model_year': forms.TextInput(attrs={'placeholder': datetime.datetime.now().year}),
            'purchase_year': forms.TextInput(attrs={'placeholder': datetime.datetime.now().year}),
            'purchase_price': forms.TextInput(attrs={'placeholder': 'Purchase price'}),
            'gone_year': forms.TextInput(attrs={'placeholder': datetime.datetime.now().year}),
        }
        help_texts = {
            'make': _('Manufacturer of vehicle.'),
            'model_name': _('Model of vehicle.'),
            'model_year': _('Model year of vehicle.'),
            'type': _('Type of vehicle.'),
            'fuel': _('Fuel used by vehicle.'),
            'purchase_year': _('Year this vehicle was purchased.'),
            'purchase_price': _('Purchase price of vehicle.'),
            'purchase_type': _('Indicate if vehicle was new or used at purchase.'),
            'finance': _('Indicate how vehicle was financed at time of purchase.'),
            'satisfaction': _('Indicate how satisfied you are with this vehicle.'),
            'status': _('Indicate the current status of this vehicle.'),
            'gone_year': _('Year you sold/retired this vehicle.'),
        }

    def clean_model_year(self):
        data = self.cleaned_data.get('model_year')
        if data > datetime.datetime.now().year + 1 or data < datetime.datetime.now().year - 100:
            self.add_error('model_year', 'Please specify a valid model year.')
        return data

    def clean_purchase_year(self):
        data = self.cleaned_data.get('purchase_year')
        if data > datetime.datetime.now().year:
            self.add_error('purchase_year', 'Cannot specify a year in the future.')
        if data < datetime.datetime.now().year - 90:
            self.add_error('purchase_year', 'Cannot specify a year that far in the past.')
        return data

    def clean_purchase_price(self):
        data = self.cleaned_data.get('purchase_price')
        if data < 1.00:
            self.add_error('purchase_price', 'Purchase price must be a minimum of $1.00.')
        return data

    def clean_gone_year(self):
        data = self.cleaned_data.get('gone_year')
        if data > datetime.datetime.now().year:
            self.add_error('gone_year', 'Cannot specify a year in the future.')
        return data

    def clean(self):
        if 'vehicle_gone_year' in self.cleaned_data and 'vehicle_purchase_year' in self.cleaned_data:
            if not self.cleaned_data['vehicle_gone_year'] == None:
                if self.cleaned_data['vehicle_gone_year'] < self.cleaned_data['vehicle_purchase_year']:
                    self.add_error('vehicle_gone_year', "A vehicle cannot be disposed of before purchase.")
