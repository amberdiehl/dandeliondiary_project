from django.forms import formset_factory, modelformset_factory
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render, render_to_response, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from .forms import *
from .models import *
from core.models import BudgetModel, VehicleMake, VehicleModel
from account.models import Account
from helpers import *

import datetime


"""
    Some of these views use a dynamic layout technique which enables a single or double columm of data.
    The layout is defined by passing an array of values for each data element:

    b = begins a shared row
    e = ends a shared row
    d = ends shared row and writes a divider
    - = sits in its own row
"""


@login_required
def household_dashboard(request):
    """Provide user with summary and status of account information. This is for ALL users associated with the
    household. Only the household owner can make changes and invite/manage other associated with the household.
    """

    # Dictionary that will contain all information for the template; no form
    summary = {}

    # Get basic user account info
    user = request.user
    account = Account.objects.get(user_id=request.user.pk)

    # Show user information on file, or request entry
    if not user.first_name:
        summary['need_myinfo'] = "Please take a moment to provide your name and a phone number."
    else:
        household_member = Member.objects.get(account=account)
        summary['first_name'] = user.first_name
        summary['last_name'] = user.last_name
        summary['phone_number'] = household_member.phone_number
        isowner = 'No'
        if household_member.owner:
            isowner = 'Yes'
        summary['owner'] = isowner

    # Show summary of select household information; if missing indicate it is necessary in order to use Dande
    try:
        membership = HouseholdMembers.objects.get(member_account=account.pk)
        household = RVHousehold.objects.get(pk=membership.household_membership)

        summary['start_year'] = household.start_year
        summary['members_in_household'] = household.members_in_household
        summary['rig_type'] = household.rig_type
        summary['use_type'] = household.use_type
        summary['children'] = household.children
        summary['pets'] = household.pets_dog + household.pets_cat + household.pets_other

    except ObjectDoesNotExist:
        household = None
        summary['need_household'] = "To activiate your trial, please setup your household information."

    # Show summary of vehicle information; if missing indicate it is desirable to provide
    if household:
        try:
            vehicles = Vehicle.objects.filter(household=membership.household_membership).exclude(gone_year__gt=0)
            summary['total_vehicles'] = len(vehicles)
            summary_of_vehicles = []
            for vehicle in vehicles:
                summary_of_vehicles.append('{} {} {}'.format(vehicle.model_year, vehicle.make, vehicle.model_name))
            summary['vehicles'] = summary_of_vehicles
        except ObjectDoesNotExist:
            summary['need_vehicles'] = "Please specify details regarding your rig. Although not required, it will " \
                                       "greatly improve Dande's ablity to provide comparative data."

    # Show subscription status
    if household:

        summary['paid_through'] = household.paid_through

        if datetime.date.today() > household.paid_through:
            summary['expired'] = "Your subscription has expired. Please renew today! Questions? " \
                                 "Call us at 415-413-4393."
        else:
            future_date = datetime.date.today() + datetime.timedelta(days=45)
            if future_date >= household.paid_through:
                summary['need_payment'] = "Your subscription will expire soon! Please renew today!"

        payments = Payment.objects.filter(household=membership.household_membership)
        if payments:
            # provide last payment information
            pass
        else:
            summary['free_trial'] = "Enjoy your free trial!"

    # Provide a Dande greeting
    if household and user.first_name:
        join_date = household.created_date
        summary['greeting'] = 'Hi {}! Thank you for being a Dande subscriber since {}.'\
            .format(user.first_name, household.created_date.strftime('%B %Y'))

    context = {
        'page_title': 'Household Dashboard',
        'url': 'household:household_dashboard',
        'summary': summary,
    }

    return render(request, 'household/household_dashboard.html', context)


@login_required
def my_info(request):
    """
    Maintain member name, phone number; indicate household ownership
    :param request:
    :return:
    """
    instructions = None  # No special instructions for the form

    # get native Django authenticated user information, and account
    user = request.user
    user_pk = request.user.pk
    account = Account.objects.get(user_id=user_pk)

    # bind form for update or enable new user setup
    bound_data = {}
    try:
        household_member = Member.objects.get(account=account)
        bound_data = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': household_member.phone_number,
            'owner': household_member.owner,
        }
    except ObjectDoesNotExist:
        pass

    if request.method == 'POST':

        # since owner checkbox is disabled, we need to hack post and keep value
        post_data = request.POST.copy()
        if not bound_data:
            post_data['owner'] = True
        else:
            post_data['owner'] = bound_data['owner']
        form = MyInfoForm(post_data)

        if form.is_valid():

            if not bound_data:
                household_member = Member()  # instantiate object for new household member

            # Save first and last name in Django user
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()

            # Create household owner
            household_member.account = account
            household_member.phone_number = form.cleaned_data.get('phone_number')
            household_member.owner = form.cleaned_data.get('owner')
            household_member.save()

            messages.success(request, 'Your information has been saved.')

        else:

            messages.warning(request, "Please fix the errors noted below.")

    else:

        if bound_data:
            form = MyInfoForm(bound_data)
        else:
            form = MyInfoForm(initial={'owner': True})

    context = {
        'form': form,
        'page_title': 'My Info',
        'url': 'household:my_info',
        'instructions': instructions,
        'layout': ['b', 'e', 'b', 'e', ],
    }

    return render(request, 'household/simple_form.html', context)


@login_required
def household_profile(request):
    """
    Creates/maintains household profile and association with household owner.
    """
    instructions = 'Please enter the information requested below. We only use this data to support setting up your ' \
                   'budget and anonymously when comparing your expenses to others to suggest ways to save money.'

    # get native Django authenticated user information, and account
    user_pk = request.user.pk
    account = Account.objects.get(user_id=user_pk)

    # get household for update, otherwise a new one is created
    try:
        membership = HouseholdMembers.objects.get(member_account=account.pk)
        household = RVHousehold.objects.get(pk=membership.household_membership)
    except ObjectDoesNotExist:
        membership = None

    if request.method == 'POST':

        if membership:
            form = HouseholdProfileForm(request.POST, instance=household)
        else:
            form = HouseholdProfileForm(request.POST)

        if form.is_valid():

            if membership:

                form.save()
                messages.success(request, 'Your information has been saved.')

            else:

                new_household = form.save(commit=False)
                new_household.budget_model = BudgetModel.objects.get(pk=1)  # default to DandelionDiary starter model
                new_household.paid_through = "2017-06-30"  # default to trial period
                new_household.save()

                # Associate new household with member account
                membership = HouseholdMembers()  # instantiate object to place account (member) in a household
                membership.member_account = account
                membership.household_membership = new_household
                membership.save()

                # Setup budget template
                setup_budget_template(new_household.budget_model.pk, new_household)

                messages.success(request, 'Your household and budget template have been created.')

        else:

            messages.warning(request, "Please fix the errors noted below.")

    else:

        if membership:
            form = HouseholdProfileForm(instance=household)
        else:
            form = HouseholdProfileForm(initial={'opt_in_contribute': True})

    context = {
        'form': form,
        'page_title': 'Household Profile',
        'url': 'household:maintain_household',
        'instructions': instructions,
        'layout': ['-', 'b', 'e', 'b', 'e', '-', 'b', 'e', '-', 'b', 'e', 'b', 'd', '-', ],
    }

    return render(request, 'household/simple_form.html', context)


@login_required
def household_vehicles(request):
    """
    Maintain all vehicles associated with the household
    :param request:
    :return:
    """
    instructions = 'Please specify vehicles associated with your household. This information helps Dande help you ' \
                   'to keep your budget on track and is very important when using the Contribute tool.'

    # get native Django authenticated user, and account
    user_pk = request.user.pk
    account = Account.objects.get(user_id=user_pk)

    # get household for vehicles
    try:
        membership = HouseholdMembers.objects.get(member_account=account)
    except ObjectDoesNotExist:
        return redirect('household:household_dashboard')

    VehicleFormSet = modelformset_factory(Vehicle, form=VehicleForm,
                                          fields=('make', 'model_name', 'model_year', 'type', 'fuel', 'purchase_year',
                                                  'purchase_price', 'purchase_type', 'finance', 'satisfaction',
                                                  'status', 'gone_year', ),
                                          can_delete=True, extra=1,)

    if request.method == 'POST':

        formset = VehicleFormSet(request.POST)

        if formset.is_valid():
            for ndx, form in enumerate(formset):
                if form.is_valid() and not form.empty_permitted:

                    if ndx in formset._deleted_form_indexes:
                        messages.warning(
                            request,
                            "The {} {} {} vehicle has been deleted.".format(form.cleaned_data.get('model_year'),
                            form.cleaned_data.get('make'),
                            form.cleaned_data.get('model_name'))
                        )
                        formset.save()

                    else:

                        if form.changed_data:
                            form.save()
                            messages.success(request, 'Your information has been saved.')

                else:

                    if form.changed_data:
                        new_vehicle = form.save(commit=False)
                        new_vehicle.household = membership.household_membership
                        new_vehicle.save()
                        messages.success(request, 'Your vehicle has been added.')

            return redirect('household:maintain_vehicles')

        else:

            messages.warning(request, "Please fix the errors found for one of your vehicles.")

    else:

        formset = VehicleFormSet(queryset=Vehicle.objects.filter(household=membership.household_membership))

        # For existing vehicles, limit model choices to associated make
        for ndx, form in enumerate(formset):
            if ndx < len(formset.forms)-1:
                form.fields['model_name'].queryset=VehicleModel.objects.filter(make=form.initial['make'])

        # Override Django to ensure new form appears to have no changes
        formset.forms[len(formset.forms)-1].changed_data=[]

    context = {
        'formset': formset,
        'url': 'household:maintain_vehicles',
        'instructions': instructions,
        'layout': ['b', 'e', '-', 'b', 'e', 'b', 'e', 'b', 'e', '-', 'b', 'e', 'b', 'e', ],
    }

    return render(request, 'household/vehicles.html', context)


def ajax_models_by_make(request, make_id):
    make = VehicleMake.objects.get(pk=make_id)
    models = VehicleModel.objects.filter(make=make)
    return render_to_response('ajax_models.html', {'models':models}, content_type='text/html')
