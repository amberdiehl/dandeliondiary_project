import datetime
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.models import User

from core.models import RigType, UseType, IncomeType, VehicleMake, VehicleModel, VehicleType, VehiclePurchaseType, \
    VehicleStatus, Satisfaction, BudgetGroup, BudgetCategory
from household.models import Household, HouseholdMembers
from compare.models import MyBudgetGroup, MyBudgetCategory
from account.models import Account

"""
Helpers related to household views and constructs.
These helpers may also be used across Compare, and Capture
"""

# Determine if module can be used; i.e. household must be setup first.
def helper_get_me(user_key):
    me = {}
    try:
        # Get account and household information first to throw error as soon as possible
        account = Account.objects.get(user_id=user_key)
        member = HouseholdMembers.objects.get(member_account=account)
        me['household_key'] = member.household_membership.pk
        me['account_obj'] = account

        # Ensure account is paid for (active)
        household = Household.objects.get(pk=member.household_membership.pk)
        me['household_obj'] = household
        if datetime.date.today() > household.paid_through:

            me['redirect'] = True

        else:

            person = User.objects.get(pk=user_key)
            me['first_name'] = person.first_name
            me['last_name'] = person.last_name

    except ObjectDoesNotExist:
        me['redirect'] = True

    return me


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
