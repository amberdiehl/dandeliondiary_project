from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.forms import modelformset_factory

from django.contrib.auth.models import User, Group

from .forms import *
from .models import *
from core.models import BudgetModel, VehicleType, VehicleMake, VehicleModel

from core.helpers import login_required_ajax
from helpers import *

import datetime

INVITE_EXPIRATION = 24  # hours
SUBSCRIPTION_LAPSE_WARNING = 45  # days


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
    household. Only the household owner can invite/manage other associated with the household.

    NOTE: This dashboard is NOT passive. New users are directed here first so that household and associated
    member, membership, and budget records can be created.
    """

    # Dictionary that will contain all information for the template; no form
    summary = {}

    # Get basic user account info
    user = request.user
    account = Account.objects.get(user_id=request.user.pk)

    # 1. If user is new member of household, automatically create associations for Member, HouseholdMember
    #    This MUST be executed FIRST to ensure the rest of the dashboard/household setup functions correctly.
    try:
        invited_member = HouseholdInvite.objects.get(email=user.email)
    except ObjectDoesNotExist:
        pass
    else:
        helper_new_member(invited_member, account)

    # 2. Show user information on file, or request entry
    try:
        household_member = Member.objects.get(account=account)
    except ObjectDoesNotExist:
        summary['need_myinfo'] = "Please take a moment to provide your name and a phone number."
    else:
        summary['first_name'] = user.first_name
        summary['last_name'] = user.last_name
        summary['phone_number'] = household_member.phone_number
        is_owner = 'No'
        if household_member.owner:
            is_owner = 'Yes'
        summary['owner'] = is_owner
        if not user.first_name or not user.last_name or not household_member.phone_number:
            summary['myinfo'] = "Please take a moment to provide your name and a phone number."

    # 3. Show summary of select household information; if missing indicate it is necessary for use
    try:
        membership = HouseholdMembers.objects.get(member_account=account.pk)
        household = RVHousehold.objects.get(pk=membership.household_membership)
    except ObjectDoesNotExist:
        household = None
        summary['need_household'] = "To activate your free trial, please setup your household information."
    else:
        summary['start_year'] = household.start_year
        summary['members_in_household'] = household.members_in_household
        summary['rig_type'] = household.rig_type
        summary['use_type'] = household.use_type
        summary['children'] = household.children
        summary['pets'] = household.pets_dog + household.pets_cat + household.pets_other

    if household:
        # 4. Show summary of vehicle information; if missing indicate it is desirable to provide
        vehicles = Vehicle.objects.filter(household=membership.household_membership).exclude(gone_year__gt=0)
        if len(vehicles) == 0:
            summary['need_vehicles'] = "Please specify details regarding your rig to enable comparative data."
        else:
            summary['total_vehicles'] = len(vehicles)
            summary_of_vehicles = []
            for vehicle in vehicles:
                summary_of_vehicles.append('{} {} {}'.format(vehicle.model_year, vehicle.make, vehicle.model_name))
            summary['vehicles'] = summary_of_vehicles

        # 5. Show subscription status
        summary['paid_through'] = household.paid_through

        if datetime.date.today() > household.paid_through:
            summary['expired'] = "Your subscription has expired. Please renew today! Questions? " \
                                 "Call us at 415-413-4393."
        else:
            future_date = datetime.date.today() + datetime.timedelta(days=SUBSCRIPTION_LAPSE_WARNING)
            if future_date >= household.paid_through:
                summary['need_payment'] = "Your subscription will expire soon! Please renew today!"

        payments = Payment.objects.filter(household=membership.household_membership)
        if payments:
            # provide last payment information
            pass
        else:
            summary['free_trial'] = "Enjoy your free trial!"

        # 6. Provide a greeting
        if user.first_name:
            summary['greeting'] = 'Hi {}! Thank you for being a subscriber since {}.'\
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

            # Place in 'forum_customers' for access to 'Contribute'
            group = Group.objects.get(name='forum_customers')
            group.user_set.add(user)

            # Create/update household member record; when new household, this creates household owner
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
        'password_link': True,
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
        'password_link': False,
    }

    return render(request, 'household/simple_form.html', context)


@login_required
def household_members(request):
    """
    Show current household members and (future) enable them to be removed (disabled now?)
    Show pending invitations to join the household and enable resend of invite
    Invite new household members
    :param request:
    :return:
    """
    # get native Django authenticated user information, account and household info
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')

    if not me['owner']:
        return redirect('household:household_dashboard')

    # get members of the household
    current = User.objects.filter(account__householdmembers__household_membership=me.get('household_key'))\
        .values('username', 'first_name', 'last_name', 'email', 'is_active', 'last_login')

    # get (and delete) pending invitations
    pending = HouseholdInvite.objects.filter(invite_household=me.get('household_key'))\
        .values('id', 'email', 'invite_date')

    # invite new members
    if request.method == 'POST':

        invite_form = InviteMemberForm(request.POST)

        if invite_form.is_valid():

            invite = HouseholdInvite()
            invite.invite_household = me.get('household_obj')
            invite.email = invite_form.cleaned_data.get('email')
            invite.security_code = get_random_string(length=7)
            invite.save()

            (code, msg) = helper_send_invite(invite.email, me, INVITE_EXPIRATION)
            if code == 'ERR':
                messages.warning(request, msg)
            else:
                messages.success(request, msg)

        else:
            pass

    else:
        invite_form = InviteMemberForm()


    context = {
        'current': current,
        'pending': pending,
        'invite_form': invite_form,
        'is_owner': me['owner'],
        'username': me['username'],
        'page_title': 'Household Members',
        'url': 'household:maintain_members',
    }

    return render(request, 'household/members.html', context)


@login_required
def household_vehicles(request):
    """
    Maintain all vehicles associated with the household
    :param request:
    :return:
    """
    instructions = 'Please specify vehicles associated with your household. This information is used to refine ' \
                   'expense Capture choices and to create "apples to apples" comparisons in the Contribute tool.'

    # get native Django authenticated user, and account
    user_pk = request.user.pk
    account = Account.objects.get(user_id=user_pk)

    # get household for vehicles
    try:
        membership = HouseholdMembers.objects.get(member_account=account)
    except ObjectDoesNotExist:
        return redirect('household:household_dashboard')

    VehicleFormSet = modelformset_factory(Vehicle, form=VehicleForm,
                                          fields=('type', 'make', 'model_name', 'model_year', 'fuel', 'purchase_year',
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

        for ndx, form in enumerate(formset):
            form.fields['type'].queryset = VehicleType.objects.all().order_by('type')
            # For existing vehicles, limit selections; make by type, and model by make.
            if ndx < len(formset.forms)-1:
                vehicle_type = VehicleType.objects.get(pk=form.initial['type'])
                form.fields['make'].queryset=VehicleMake.objects.filter(filter=vehicle_type.filter)
                form.fields['model_name'].queryset=VehicleModel.objects.filter(make=form.initial['make'])
            else:
                # Make dependent selections empty and override Django to ensure new form has no changes
                form.fields['make'].queryset = VehicleMake.objects.filter(pk=0)
                form.fields['model_name'].queryset = VehicleModel.objects.filter(pk=0)
                form.changed_data=[]

    context = {
        'formset': formset,
        'url': 'household:maintain_vehicles',
        'instructions': instructions,
        'layout': ['-', 'b', 'e', 'b', 'e', 'b', 'e', 'b', 'e', '-', 'b', 'e', 'b', 'e', ],
    }

    return render(request, 'household/vehicles.html', context)


def ajax_models_by_make(request, make_id):
    make = VehicleMake.objects.get(pk=make_id)
    models = VehicleModel.objects.filter(make=make)
    response_data = "{"
    for ndx, model in enumerate(models):
        if ndx > 0:
            response_data += ','
        response_data += '"{}": "{}"'.format(model.id, model.model_name)
    response_data += "}"
    return JsonResponse(response_data, safe=False)


def ajax_makes_by_type(request, type_id):
    type = VehicleType.objects.get(pk=type_id)
    makes = VehicleMake.objects.filter(filter=type.filter)
    response_data = "{"
    for ndx, make in enumerate(makes):
        if ndx > 0:
            response_data += ','
        response_data += '"{}": "{}"'.format(make.id, make.make)
    response_data += "}"
    return JsonResponse(response_data, safe=False)


@login_required_ajax
def ajax_add_make(request, type_key, make):

    result = {}

    try:
        type = VehicleType.objects.get(pk=type_key)
    except ObjectDoesNotExist:
        result['status'] = 'ERROR'
        return JsonResponse(result)

    # Force case for make for consistency
    make = make.title()

    try:
        m = VehicleMake.objects.get(make=make)
    except ObjectDoesNotExist:

        new_make = VehicleMake()
        new_make.filter = type.filter
        new_make.make = make
        new_make.save()

        result['status'] = 'OK'
        result['new'] = True
        result['make'] = make
        result['key'] = new_make.pk

    else:

        result['status'] = 'OK'
        result['new'] = False
        result['key'] = m.pk

    return JsonResponse(result)


@login_required_ajax
def ajax_add_model(request, make_key, model):

    result = {}

    try:
        make = VehicleMake.objects.get(pk=make_key)
    except ObjectDoesNotExist:
        result['status'] = 'ERROR'
        return JsonResponse(result)

    # Force case for model for consistency
    model = model.title()

    try:
        m = VehicleModel.objects.get(model_name=model)
    except ObjectDoesNotExist:

        new_model = VehicleModel()
        new_model.make = make
        new_model.model_name = model
        new_model.save()

        result['status'] = 'OK'
        result['new'] = True
        result['model'] = model
        result['key'] = new_model.pk

    else:

        result['status'] = 'OK'
        result['new'] = False
        result['key'] = m.pk

    return JsonResponse(result)


@login_required_ajax
def ajax_delete_invite(request):
    """
    Deletes a pending invite request at the request of the household owner. Rather than deleting directly if id
    is valid, verifies household associated with id is also associated with username supplied.
    :param request:
    :return:
    """

    result = {}

    id = request.POST['id']
    username = request.POST['user']

    try:
        invite = HouseholdInvite.objects.get(pk=id)
    except ObjectDoesNotExist:
        result['status'] = 'ERROR'
        return JsonResponse(result)

    user = User.objects.filter(account__householdmembers__household_membership=invite.invite_household)\
        .filter(username=username)
    if len(user) != 1:
        result['status'] = 'ERROR'
        return JsonResponse(result)

    invite.delete()
    result['status'] = 'OK'
    return JsonResponse(result)


@login_required_ajax
def ajax_change_member_status(request):

    result = {}

    username = request.POST['username']
    owner_username = request.POST['user']
    change_to_status = request.POST['status']

    try:
        member = User.objects.get(username=username)
    except ObjectDoesNotExist:
        result['status'] = 'ERROR'
        return JsonResponse(result)

    mbr_account = Account.objects.get(user_id=member)
    mbr_household = HouseholdMembers.objects.get(member_account=mbr_account)

    owner = User.objects.get(username=owner_username)
    owner_account = Account.objects.get(user_id=owner)
    owner_household = HouseholdMembers.objects.get(member_account=owner_account)

    if mbr_household.household_membership != owner_household.household_membership:
        result['status'] = 'ERROR'
        return JsonResponse(result)

    if change_to_status == 'Deactivate':
        new_status = False
    else:
        new_status = True

    member.is_active = new_status
    member.save()
    result['status'] = 'OK'
    return JsonResponse(result)
