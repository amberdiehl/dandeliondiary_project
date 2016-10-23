import datetime
from django.db.models import F, Sum
from compare.models import MyBudgetGroup, MyBudgetCategory, MyBudget
from .models import MyExpenseItem


def helper_categories_without_geo(household):
    """
    Without help from geolocation services, need to return entire list of categories for selection.
    Group is used to create tiered organization and cannot be selected. Child categories are collapsed with
    their parents; but it is the child key that is used so that expenses are associated with them.

    Categories names are shortened if they contain "(e.g. ...)".

    The comma located at the end of each tuple add is what causes python to create tuples in tuples.
    """

    all_choices = ()

    groups = MyBudgetGroup.objects.filter(household=household).order_by('group_list_order')
    for ndx, group in enumerate(groups):

        choices = ()

        categories = MyBudgetCategory.objects.filter(my_budget_group=group).filter(parent_category=None)\
            .order_by('my_category_name')
        for category in categories:
            children = MyBudgetCategory.objects.filter(parent_category=category).order_by('my_category_name')
            if children:
                for child in children:
                    choice = (child.pk, display_name(category.my_category_name) + ' - ' +
                              display_name(child.my_category_name))
                    choices += choice,
            else:
                choice = (category.pk, display_name(category.my_category_name))
                choices += choice,

        group_choices = (group.my_group_name, choices)
        if ndx == 0:
            all_choices += (0, '------'),
        all_choices += group_choices,

    return all_choices


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
