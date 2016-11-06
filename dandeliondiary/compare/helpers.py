import datetime
from django.db.models import F, Sum
from capture.models import MyExpenseItem
from .models import MyBudgetCategory, MyBudget

"""
Includes MyExpenseItem helpers to prevent circular references which are not supported in this version of Python.
"""


def helper_get_category_budget_and_expenses(category, filter_date=None, fetch_expenses=False):

    budget_amount = 0
    expense_total = 0

    if not filter_date:
        filter_date = datetime.date.today()

    children = MyBudgetCategory.objects.filter(parent_category=category)
    if children:

        for child in children:
            child_budgets = MyBudget.objects.filter(category=child)\
                .filter(effective_date__year__lte=filter_date.year, effective_date__month__lte=filter_date.month)\
                .order_by('-effective_date')
            if child_budgets:
                budget_amount += child_budgets[0].amount

            if fetch_expenses:
                expense_total += get_expenses_for_period(child, from_date=filter_date)

    else:

        category_budgets = MyBudget.objects.filter(category=category) \
            .filter(effective_date__year__lte=filter_date.year, effective_date__month__lte=filter_date.month) \
            .order_by('-effective_date')
        if category_budgets:
            budget_amount = category_budgets[0].amount

        if fetch_expenses:
            expense_total = get_expenses_for_period(category, from_date=filter_date)

    return {'budget': budget_amount, 'expenses': expense_total}


def helper_get_group_budget_and_expenses(group, filter_date=None):
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


def get_expenses_for_period(category, from_date=None, to_date=None):

    if not from_date:
        from_date = datetime.date.today()

    if not to_date:
        to_date = from_date

    expenses = MyExpenseItem.objects.filter(category=category) \
        .filter(expense_date__year__gte=from_date.year, expense_date__month__gte=from_date.month) \
        .filter(expense_date__year__lte=to_date.year, expense_date__month__lte=to_date.month) \
        .aggregate(Sum('amount'))
    if expenses.get('amount__sum') == None:
        expense_total = 0
    else:
        expense_total = expenses.get('amount__sum')

    return expense_total
