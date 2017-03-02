import datetime
import re
from decimal import *
from django.db.models import F, Sum
from capture.models import MyExpenseItem
from .models import MyBudgetCategory, MyBudget

RE_VALID_GROUP_NAME = re.compile(r'^[\w \+]{1,20}$')
RE_VALID_GROUP_DESCRIPTION = re.compile(r'^[\w .,]{0,256}$')
RE_VALID_GROUP_ORDER = re.compile(r'^\d*$')
RE_VALID_CATEGORY_NAME = re.compile(r'^[\w (,)\+.]{1,50}$')
RE_VALID_BUDGET_AMOUNT = re.compile(r'^[\d.]+$')
RE_VALID_BUDGET_ANNUAL_MONTH = re.compile(r'^\d{1,2}$')
RE_VALID_BUDGET_NOTE = re.compile(r'^[\w\d ,.\-=()/*\+]{0,512}$')
RE_VALID_BUDGET_EFFECTIVE_DATE = re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$')
RE_VALID_HASH_KEY = re.compile(r'^[\w\d]{16}$')

"""
Includes MyExpenseItem helpers to prevent circular references which are not supported in this version of Python.
"""


def helper_get_category_budget_and_expenses(category, filter_date=None, fetch_expenses=False, convert_annual=False):
    """
    Reminder that filter_date is used to get budget record effective for period (month) user selected and should be
    setup as last day of the month.

    :param category: Expense category
    :param filter_date: Used to determine correct budget to retrieve
    :param fetch_expenses: Indicate if only budget info or to include expenses too
    :param convert_annual: Indicate if an annual budget amount should be returned as monthly rate
    :return:
    """

    budget_amount = 0
    expense_total = 0

    if not filter_date:
        filter_date = datetime.date.today()

    children = MyBudgetCategory.objects.filter(parent_category=category)
    if children:

        for child in children:
            child_budgets = MyBudget.objects.filter(category=child).filter(effective_date__lte=filter_date)\
                .order_by('-effective_date')
            if child_budgets:
                budget = child_budgets[0].amount

                if child_budgets[0].annual_payment_month > 0:
                    if convert_annual:
                        monthly_amount = Decimal(budget / 12)
                        budget = Decimal(monthly_amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
                    else:
                        if not child_budgets[0].annual_payment_month == filter_date.month:
                            budget = 0

                budget_amount += budget

            if fetch_expenses:
                expense_total += get_expenses_for_period(child, from_date=filter_date)

    else:

        category_budgets = MyBudget.objects.filter(category=category).filter(effective_date__lte=filter_date) \
            .order_by('-effective_date')
        if category_budgets:
            budget = category_budgets[0].amount

            if category_budgets[0].annual_payment_month > 0:
                if convert_annual:
                    monthly_amount = Decimal(budget / 12)
                    budget = Decimal(monthly_amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
                else:
                    if not category_budgets[0].annual_payment_month == filter_date.month:
                        budget = 0

            budget_amount = budget

        if fetch_expenses:
            expense_total = get_expenses_for_period(category, from_date=filter_date)

    return {'budget': budget_amount, 'expenses': expense_total}


def helper_get_group_budget_and_expenses(group, filter_date=None, fetch_expenses=True):
    """
    Get and return budget for a group.
    :param group:
    :param filter_date:
    :param fetch_expenses:
    :return:
    """

    group_budget = 0
    group_expenses = 0

    categories = MyBudgetCategory.objects.filter(my_budget_group=group).filter(parent_category=None)
    for category in categories:
        amounts = helper_get_category_budget_and_expenses(category, filter_date=filter_date,
                                                          fetch_expenses=fetch_expenses)
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


def get_month_options():
    """
    Options list returns last day of every month. This is so that any effective date for a given budget for a given
    month is included for the whole month. Since month's are not split it's not possible to accurately report expenses
    for a given month falling before or after a date in the middle of the month. Also, it is assumed users will create
    new budgets to be effective at the beginning of a month; e.g. 5/1/2017.
    :return:
    """
    options = []

    # Seed date to be the last day of this month.
    this_month = datetime.date.today().replace(day=1)
    future_date = this_month + datetime.timedelta(days=32)
    dt = future_date.replace(day=1) - datetime.timedelta(days=1)

    while True:
        option = (dt.strftime('%Y-%m-%d'), dt.strftime("%B"))
        options.append(option)
        if len(options) == 12:
            break
        dt = dt.replace(day=1) - datetime.timedelta(days=1)
    return options


def validate_group_inputs(name, description, order):
    if re.match(RE_VALID_GROUP_NAME, name) and re.match(RE_VALID_GROUP_DESCRIPTION, description) and \
            re.match(RE_VALID_GROUP_ORDER, order):
        return True
    else:
        return False


def validate_category_name_input(name):
    if re.match(RE_VALID_CATEGORY_NAME, name):
        return True
    else:
        return False


def validate_budget_inputs(amount, month, note, date):
    if re.match(RE_VALID_BUDGET_AMOUNT, amount) \
            and re.match(RE_VALID_BUDGET_ANNUAL_MONTH, month) \
            and re.match(RE_VALID_BUDGET_NOTE, note) \
            and re.match(RE_VALID_BUDGET_EFFECTIVE_DATE, date):
        return True
    else:
        return False


def validate_id_input(hashed_id):
    if re.match(RE_VALID_HASH_KEY, hashed_id):
        return True
    else:
        return False
