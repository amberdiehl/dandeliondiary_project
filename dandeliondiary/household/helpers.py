import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail

from django.contrib.auth.models import User
from account.models import Account

from core.models import BudgetGroup, BudgetCategory
from household.models import Household, HouseholdMembers, Member
from compare.models import MyBudgetGroup, MyBudgetCategory

"""
Helpers related to household views and constructs.
These helpers may also be used across Compare, and Capture
"""


# Determine if module can be used; i.e. household must be setup first, subscription active.
def helper_get_me(user_key):
    me = {}
    try:
        # Get account and household information first to throw error as soon as possible
        account = Account.objects.get(user_id=user_key)
        membership = HouseholdMembers.objects.get(member_account=account)
        me['household_key'] = membership.household_membership.pk
        me['account_obj'] = account

        # Ensure account is paid for (active)
        household = Household.objects.get(pk=membership.household_membership.pk)
        me['household_obj'] = household
        if datetime.date.today() > household.paid_through:

            me['redirect'] = True
            me['error_message'] = 'Subscription expired.'

        else:

            # User is/is not owner of household
            member = Member.objects.get(account=account)
            me['owner'] = member.owner

            person = User.objects.get(pk=user_key)
            me['username'] = person.username
            me['first_name'] = person.first_name
            me['last_name'] = person.last_name

    except ObjectDoesNotExist:
        me['redirect'] = True
        me['error_message'] = 'Household must be created first.'

    return me


# Send household invitation email
def helper_send_invite(email, me, expiration):

    subject = '{} invites you to Dandelion Diary'.format(me.get('first_name').title())
    body = "Hello! This is an invitation from {0} {1} to create an account with Dandelion Diary and join " \
           "{0}'s household. This invitation will expire in {2} hours. To accept, please " \
           "get started here: https://www.dandeliondiary.com/account/signup/." \
        .format(me.get('first_name').title(), me.get('last_name').title(), expiration)

    try:
        send_mail(subject, body, 'noresponse@dandeliondiary.com', [email], fail_silently=False)

    except:
        return 'ERR', 'Invitation email failed to send; please contact Support for assistance.'

    return 'OK', 'An invitation has been sent and will expire in {} hours.'.format(expiration)


# Setup budget template for new household
def setup_budget_template(budget_template_id, household_id):
    """
    To setup the budget template for a household, we need to iterate in through the items in hierarchy to keep the
    correct relationships between budget groups, categories and sub-categories.

    At this time there are no child-child relationships to keep things simple.
    :param budget_template_id:
    :param household_id:
    :return:
    """
    groups = BudgetGroup.objects.filter(budget_model=budget_template_id)
    for group in groups:
        my_group = MyBudgetGroup()
        my_group.household = household_id
        my_group.my_group_name = group.group_name
        my_group.group_description = group.group_description
        my_group.group_perma_key = group.group_perma_key
        my_group.group_list_order = group.group_list_order
        my_group.save()

        categories = BudgetCategory.objects.filter(budget_group=group).filter(parent_category__isnull=True)
        for category in categories:
            my_category = MyBudgetCategory()
            my_category.my_budget_group = my_group
            my_category.my_category_name = category.category
            # we allow my_category.parent_category to default to null
            my_category.category_perma_key = category.category_perma_key
            my_category.save()

            child_categories = BudgetCategory.objects.filter(parent_category=category)
            for child in child_categories:
                my_child_category = MyBudgetCategory()
                my_child_category.my_budget_group = my_group
                my_child_category.my_category_name = child.category
                my_child_category.parent_category = my_category
                my_child_category.category_perma_key = child.category_perma_key
                my_child_category.save()


# Create Member and HouseholdMembers records for new member of a household.
def helper_new_member(invite, account):

    # Create member record; note owner flag is set to false.
    member = Member()
    member.account = account
    member.owner = False
    member.save()

    # Associate account with household from invitation
    household_member = HouseholdMembers()
    household_member.member_account = account
    household_member.household_membership = invite.invite_household
    household_member.save()

    # Delete the used invitation
    invite.delete()
