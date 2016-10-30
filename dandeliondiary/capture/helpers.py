import datetime
from django.db.models import F, Sum
from compare.models import MyBudgetGroup, MyBudgetCategory, MyBudget
from .models import MyExpenseItem
from core.helpers import helpers_get_current_location_categories


def helper_budget_categories(household, place_types=None):
    """
    Creates values to be used in both budget category choosers. If google places is found, first chooser contains
    categories associated with the places returned. These are excluded from the second chooser. When there are no
    google place values, all categories appear in second chooser only.

    This parallel approach is taken to reduce server-side processing. Rather than show a person all the places found
    it is assumed that out of the list, an approprate 'hit' will be found in the budget categories and, by showing
    them up front saves making the user select a google place found and an ajax call to create a list of categories
    that match it.

    Group is used to create tiered organization and cannot be selected. Child categories are collapsed with
    their parents, and it is the child key that is used so that expenses are associated with them.

    Category names are shortened if they contain "(e.g. ...)".

    The comma located at the end of each tuple add is what causes python to create tuples in tuples.
    """

    categories_at_this_location = helpers_get_current_location_categories(place_types)

    all_choices1 = ()  # for categories based on google places
    all_choices2 = ()  # for categories not associated with google places

    groups = MyBudgetGroup.objects.filter(household=household).order_by('group_list_order')
    for ndx, group in enumerate(groups):

        choices1 = ()
        choices2 = ()

        categories = MyBudgetCategory.objects.filter(my_budget_group=group).filter(parent_category=None)\
            .order_by('my_category_name')
        for category in categories:

            children = MyBudgetCategory.objects.filter(parent_category=category).order_by('my_category_name')
            if children:

                for child in children:

                    choice = (child.pk, display_name(category.my_category_name) + ' - ' +
                              display_name(child.my_category_name))

                    if child.category_perma_key in categories_at_this_location:
                        choices1 += choice,
                    else:
                        choices2 += choice,
            else:

                choice = (category.pk, display_name(category.my_category_name))

                if category.category_perma_key in categories_at_this_location:
                    choices1 += choice,
                else:
                    choices2 += choice,

        group_choices1 = ()
        if choices1:
            group_choices1 = (group.my_group_name, choices1)

        group_choices2 = ()
        if choices2:
            group_choices2 = (group.my_group_name, choices2)

        if ndx == 0:
            all_choices1 += (0, '------'),
            all_choices2 += (0, '------'),

        if group_choices1:
            all_choices1 += group_choices1,

        if group_choices2:
            all_choices2 += group_choices2,

    return all_choices1, all_choices2


def display_name(name):
    """
    Remove "(e.g. ...)" from category names when displaying in dropdown selection box.
    """
    pos = name.find('(')
    if pos != -1:
        return name[0:pos]
    else:
        return name


def get_remaining_budget(c_id):
    """
    Get amount remaining in category budget.
    """
    # Get current budget amount
    budget = MyBudget.objects.filter(category=c_id).order_by('-effective_date')
    if budget:
        current_budget = budget[0].amount
    else:
        current_budget = 0

    # Get current expenses already recorded for this budget, for the month
    today = datetime.date.today()
    start_date = today.replace(day=1)

    current_expenses = MyExpenseItem.objects.filter(category=c_id).filter(expense_date__gte=start_date) \
        .aggregate(Sum('amount'))
    if not current_expenses:
        current_expenses = 0

    # Note: New expense should be captured and included in 'current_expenses'
    return current_budget - current_expenses.get('amount__sum')
