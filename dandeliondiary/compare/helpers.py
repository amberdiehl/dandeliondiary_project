from django.db.models import F, Sum
from capture.helpers import get_expenses_for_period
from .models import MyBudgetCategory, MyBudget


def helper_get_category_budget_and_expenses(category, from_date=None, to_date=None, fetch_expenses=False):

    budget_amount = 0
    expense_total = -1

    children = MyBudgetCategory.objects.filter(parent_category=category)
    if children:
        for child in children:
            child_budgets = MyBudget.objects.filter(category=child).order_by('-effective_date')
            if child_budgets:
                budget_amount += child_budgets[0].amount

            if fetch_expenses:
                expense_total += get_expenses_for_period(child)

    else:

        category_budgets = MyBudget.objects.filter(category=category).order_by('-effective_date')
        if category_budgets:
            budget_amount = category_budgets[0].amount

        if fetch_expenses:
            expense_total = get_expenses_for_period(category)

    return {'budget': budget_amount, 'expenses': expense_total}


def helper_get_group_budget_and_expenses(group, effective_date=None):
    """
    Get and return budget for a group.
    :param group:
    :return:
    """

    group_budget = 0
    group_expenses = 0

    categories = MyBudgetCategory.objects.filter(my_budget_group=group).filter(parent_category=None)
    for category in categories:
        amounts = helper_get_category_budget_and_expenses(category, fetch_expenses=True)
        group_budget += amounts['budget']
        group_expenses += amounts['expenses']

    return {'group_budget': group_budget, 'group_expenses': group_expenses}
