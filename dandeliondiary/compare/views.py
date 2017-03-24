import datetime

from decimal import *
from django.forms import fields
from django.shortcuts import redirect, render, render_to_response, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum

from hashids import Hashids

from capture.helpers import helper_budget_categories
from household.helpers import helper_get_me
from .helpers import *

from .models import MyBudgetGroup, MyBudgetCategory, MyBudget

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16  # Note that this value is still hard-coded in URLs for validation


@login_required
def compare_dashboard(request):
    """
    The dashboard landing page for compare shows current graphical status of budget and expenses. It also
    triggers the creation of the budget setup when an account is first created on Dandelion.
    :param request:
    :return:
    """
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        # Send customized date range based on when subscriber started using Dandelion Diary
        years = ()
        try:
            expenses = MyExpenseItem.objects.filter(household=me.get('household_key')).order_by('expense_date')[0]
        except IndexError:
            start_year = datetime.datetime.now().year
        else:
            start_year = expenses.expense_date.year

        current_year = datetime.datetime.now().year
        for yr in range(start_year, current_year+1):
            years += yr,

        category_choices = helper_budget_categories(me.get('household_key'), top_load=True,
                                                    no_selection='All categories')
        category_chooser = fields.ChoiceField(
            choices=category_choices
        )

        context = {
            'page_title': 'Compare Dashboard',
            'url': 'compare:compare_dashboard',
            'options': get_month_options(),
            'years': sorted(years, reverse=True),
            'choose_category': category_chooser.widget.render('choose_category', 0)
        }

        return render(request, 'compare/compare_dashboard.html', context)


@login_required
def budget_and_expenses(request):
    """
    Show current (or past)budgets and associated expenses, balance.
    :param request:
    :return:
    """
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')
        group_tabs = []
        group_keys = ''
        for group in budget_groups:
            group_tabs.append(group.my_group_name)
            group_keys += hashids.encode(group.pk) + ','

        context = {
            'page_title': 'Budget + Expenses',
            'url': 'compare:budgets_expenses',
            'tabs': group_tabs,
            'keys': group_keys,
            'options': get_month_options(),
        }

        return render(request, 'compare/budget_expenses.html', context)


@login_required
def budget(request):
    """
    Define the budget for each group/category of expenses.
    :param request:
    :return:
    """
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')
        group_tabs = []
        group_keys = ''
        for group in budget_groups:
            group_tabs.append(group.my_group_name)
            group_keys += hashids.encode(group.pk) + ','

        context = {
            'page_title': 'Budget',
            'url': 'compare:budget',
            'tabs': group_tabs,
            'keys': group_keys,
        }

        return render(request, 'compare/budget.html', context)


@login_required
def groups_and_categories(request):
    """
    This page enables the user to change names for template groups and categories and to add their own groups and
    categories, if desired.
    :param request:
    :return:
    """
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        context = {
            'page_title': 'Groups and Categories',
            'url': 'compare:groups_categories',
        }

        return render(request, 'compare/groups_categories.html', context=context)


@login_required
def ajax_dashboard_snapshot(request, dt):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['status'] = 'ERROR'
        return JsonResponse(response_data)

    filter_date = datetime.datetime.strptime(dt, '%Y-%m-%d').date()

    today = datetime.datetime.now().date()
    if today.year == filter_date.year and today.month == filter_date.month:
        days_remaining = filter_date.day - today.day
    else:
        days_remaining = 0

    # setup columns for budget and expenses column chart
    budget_expense_columnchart = {}
    cols_budget_expense_columnchart = [
        {'id': 'groups', 'label': 'Groups', 'type': 'string'},
        {'id': 'budget', 'label': 'Budget', 'type': 'number'},
        {'id': 'expenses', 'label': 'Expenses', 'type': 'number'}
    ]
    rows_budget_expense_columnchart = []

    total_budget = 0
    total_expenses = 0

    budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')

    for group in budget_groups:

        amounts = helper_get_group_budget_and_expenses(group, filter_date=filter_date, fetch_expenses=True)

        total_budget += amounts['group_budget']
        total_expenses += amounts['group_expenses']

        row_budget_expense_columnchart = {'c': [{'v': group.my_group_name},
                                                {'v': int(amounts['group_budget'])},
                                                {'v': int(amounts['group_expenses'])}]}
        rows_budget_expense_columnchart.append(row_budget_expense_columnchart)

    budget_expense_columnchart['cols'] = cols_budget_expense_columnchart
    budget_expense_columnchart['rows'] = rows_budget_expense_columnchart

    response_data['status'] = 'OK'
    response_data['totalBudget'] = total_budget
    response_data['totalExpenses'] = total_expenses
    response_data['netRemaining'] = total_budget - total_expenses
    response_data['daysRemaining'] = days_remaining
    response_data['budgetExpenseColumnchart'] = budget_expense_columnchart

    return JsonResponse(response_data)


@login_required
def ajax_dashboard_month_series(request, from_date, to_date, category):
    """
    Gets the net difference of budget and expenses for a given series of months. Note that although dates require
    "day" being 01, the entire month of expenses are retrieved.

    :param request:
    :param from_date: Must use format 2016-01-01 where day is always set to 01
    :param to_date: Must use format 2016-12-01 where day is always set to 01
    :param category: If provided, s/b category key to filter results
    :return:
    """

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['status'] = 'ERROR'
        return JsonResponse(response_data)

    f_dt = datetime.datetime.strptime(from_date, '%Y-%m-%d').date()
    t_dt = datetime.datetime.strptime(to_date, '%Y-%m-%d').date()
    today = datetime.datetime.now().date()

    # setup for column chart
    column_chart = {}
    cols = [
        {'id': 'month', 'label': 'Month', 'type': 'string'},
        {'id': 'amount', 'label': 'Net Amount', 'type': 'number'},
        {'type': 'string', 'role': 'style'}
    ]
    rows = []

    this_date = f_dt

    while this_date <= t_dt:

        track_categories = []
        month_net = 0
        month_abbr = this_date.strftime('%b')
        category_key = int(category)

        if this_date <= today:

            # Select effective budget based on last day of month (period) being processed, not first day
            future_date = this_date + datetime.timedelta(days=32)
            full_month = future_date.replace(day=1) - datetime.timedelta(days=1)

            budgets = MyBudget.objects.filter(category__my_budget_group__household=me.get('household_key')) \
                .filter(effective_date__lte=full_month) \
                .values('category', 'amount', 'annual_payment_month') \
                .order_by('-effective_date')

            if category_key:
                budgets = budgets.filter(category=category_key)

            for budget in budgets:
                if budget['category'] in track_categories:
                    pass  # skip older budget record(s)
                else:
                    track_categories.append(budget['category'])
                    if budget['annual_payment_month'] == 0 or budget['annual_payment_month'] == this_date.month:
                        month_net += budget['amount']

            if not category_key:
                expenses = MyExpenseItem.objects.filter(household=me.get('household_key')) \
                    .filter(expense_date__year=this_date.year, expense_date__month=this_date.month) \
                    .aggregate(Sum('amount'))
            else:
                expenses = MyExpenseItem.objects.filter(household=me.get('household_key')) \
                    .filter(expense_date__year=this_date.year, expense_date__month=this_date.month) \
                    .filter(category=category_key) \
                    .aggregate(Sum('amount'))

            if expenses.get('amount__sum') is None:
                pass
            else:
                month_net -= expenses.get('amount__sum')

        if month_net < 0:
            color = '#FA490F'
        else:
            color = '#8EAF17'

        row = {'c': [{'v': month_abbr},
                     {'v': int(month_net)},
                     {'v': color}
                     ]}

        rows.append(row)

        this_date += datetime.timedelta(days=32)
        this_date = this_date.replace(day=1)

    column_chart['cols'] = cols
    column_chart['rows'] = rows

    response_data['status'] = 'OK'
    response_data['monthSeries'] = column_chart

    return JsonResponse(response_data)


@login_required
def ajax_dashboard_budget(request, dt):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['status'] = 'ERROR'
        return JsonResponse(response_data)

    filter_date = datetime.datetime.strptime(dt, '%Y-%m-%d').date()

    # setup columns for budget pie chart
    budget_piechart = {}
    cols_budget_piechart = [
        {'id': 'groups', 'label': 'Groups', 'type': 'string'},
        {'id': 'amount', 'label': 'Amount', 'type': 'number'}
    ]
    rows_budget_piechart = []

    total_budget = 0

    budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')

    for group in budget_groups:

        amounts = helper_get_group_budget_and_expenses(group, filter_date=filter_date, fetch_expenses=False)

        total_budget += amounts['group_budget']

        row_budget_piechart = {'c': [{'v': group.my_group_name},
                                     {'v': int(amounts['group_budget'])}]}
        rows_budget_piechart.append(row_budget_piechart)

    budget_piechart['cols'] = cols_budget_piechart
    budget_piechart['rows'] = rows_budget_piechart

    response_data['status'] = 'OK'
    response_data['totalBudget'] = total_budget
    response_data['budgetPiechart'] = budget_piechart

    return JsonResponse(response_data)


@login_required
def ajax_be_groups(request, dt):
    """
    Budgets + Expenses: Show current or past budget and expense information

    :param request:
    :param dt:
    :return:
    """
    response_data = {}

    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:

        filter_date = datetime.datetime.strptime(dt, '%Y-%m-%d').date()

        data = []

        budget_total = 0
        expense_total = 0

        budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')
        for group in budget_groups:

            record = {}
            record['group'] = group.my_group_name
            amounts = helper_get_group_budget_and_expenses(group, filter_date=filter_date)
            record['budget'] = amounts['group_budget']
            record['expense'] = amounts['group_expenses']
            record['balance'] = amounts['group_budget'] - amounts['group_expenses']
            data.append(record)

            budget_total += amounts['group_budget']
            expense_total += amounts['group_expenses']

        record = {}
        record['group'] = '<b>** Total</b>'
        record['budget'] = '<b>{}</b>'.format(budget_total)
        record['expense'] = '<b>{}</b>'.format(expense_total)
        record['balance'] = '<b>{}</b>'.format(budget_total-expense_total)
        data.append(record)

        response_data['Result'] = 'OK'
        response_data['Records'] = data

    return JsonResponse(response_data)


@login_required
def ajax_be_categories(request, pid, dt):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        this = hashids.decode(pid)[0]

        filter_date = datetime.datetime.strptime(dt, '%Y-%m-%d').date()

        data = []

        budget_total = 0
        expense_total = 0

        budget_categories = MyBudgetCategory.objects.filter(my_budget_group=this).filter(parent_category=None)\
            .order_by('my_category_name')
        for category in budget_categories:

            record = {}
            record['my_category_name'] = category.my_category_name
            amounts = helper_get_category_budget_and_expenses(category, filter_date=filter_date, fetch_expenses=True)
            record['budget'] = amounts['budget']
            record['expense'] = amounts['expenses']
            record['balance'] = amounts['budget'] - amounts['expenses']
            data.append(record)

            budget_total += amounts['budget']
            expense_total += amounts['expenses']

        record = {}
        record['my_category_name'] = '<b>** Total</b>'
        record['budget'] = '<b>{}</b>'.format(budget_total)
        record['expense'] = '<b>{}</b>'.format(expense_total)
        record['balance'] = '<b>{}</b>'.format(budget_total-expense_total)
        data.append(record)

        response_data['Result'] = 'OK'
        response_data['Records'] = data

    return JsonResponse(response_data)


@login_required
def ajax_list_groups(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:
        data = []

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')
        for group in budget_groups:
            record = {}
            record['id'] = hashids.encode(group.pk)
            record['my_group_name'] = group.my_group_name
            record['group_description'] = group.group_description
            record['group_list_order'] = group.group_list_order
            record['core'] = 'no'
            if group.group_perma_key:
                record['core'] = 'yes'
            data.append(record)

        response_data['Result'] = 'OK'
        response_data['Records'] = data

    return JsonResponse(response_data)


@login_required
def ajax_create_group(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_group_inputs(request.POST.get('my_group_name'),
                                 request.POST.get('group_description'),
                                 request.POST.get('group_list_order')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid group name, description and/or list order given.'
        return JsonResponse(response_data)

    gr_name = request.POST.get('my_group_name')
    gr_description = request.POST.get('group_description')
    gr_list_order = request.POST.get('group_list_order')

    new_group = MyBudgetGroup()
    new_group.household = me.get('household_obj')
    new_group.my_group_name = gr_name
    new_group.group_description = gr_description
    new_group.group_list_order = gr_list_order
    new_group.save()

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

    record = {}
    record['id'] = hashids.encode(new_group.pk)
    record['my_group_name'] = new_group.my_group_name
    record['group_description'] = new_group.group_description
    record['group_list_order'] = new_group.group_list_order
    response_data['Result'] = 'OK'
    response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_update_group(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_id_input(request.POST.get('id')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)
    if not validate_group_inputs(request.POST.get('my_group_name'),
                                 request.POST.get('group_description'),
                                 request.POST.get('group_list_order')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid group name, description and/or list order given.'
        return JsonResponse(response_data)

    # Get budget group for received ID and validate association with logged in user household
    id_hashed = request.POST.get('id')
    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    this = hashids.decode(id_hashed)[0]
    try:
        budget_group = MyBudgetGroup.objects.get(pk=this)
    except ObjectDoesNotExist:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Error getting budget group.'
        return JsonResponse(response_data)

    if not budget_group.household.pk == me.get('household_key'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request for budget group.'
        return JsonResponse(response_data)

    record = {}
    if not budget_group.my_group_name == request.POST.get('my_group_name'):
        budget_group.my_group_name = request.POST.get('my_group_name')
        record['my_group_name'] = request.POST.get('my_group_name')
    if not budget_group.group_description == request.POST.get('group_description'):
        budget_group.group_description = request.POST.get('group_description')
        record['group_description'] = request.POST.get('group_description')
    if not budget_group.group_list_order == request.POST.get('group_list_order'):
        budget_group.group_list_order = request.POST.get('group_list_order')
        record['group_list_order'] = request.POST.get('group_list_order')
    budget_group.save()
    response_data['Result'] = 'OK'
    response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_delete_group(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_id_input(request.POST.get('id')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    id_hashed = request.POST.get('id')
    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    this = hashids.decode(id_hashed)[0]
    try:
        budget_group = MyBudgetGroup.objects.get(pk=this)
    except ObjectDoesNotExist:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Error getting budget group.'
        return JsonResponse(response_data)

    if not budget_group.household.pk == me.get('household_key'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request for budget group.'
        return JsonResponse(response_data)

    if budget_group.group_perma_key:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Sorry, this is a core budget group used for comparisons and cannot be deleted.'
        return JsonResponse(response_data)

    budget_group.delete()
    response_data['Result'] = 'OK'

    return JsonResponse(response_data)


@login_required
def ajax_list_categories(request, s, pid):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:

        # TODO: Needs more validation.

        data = []
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        this = hashids.decode(pid)[0]

        # Get parent level categories for flags 'p'arent and 'h'ybrid
        if s == 'p' or s == 'h':
            budget_categories = MyBudgetCategory.objects.filter(my_budget_group=this).filter(parent_category=None)\
                .order_by('my_category_name')
        else:
            # Fetch 'c'hildren categories
            budget_categories = MyBudgetCategory.objects.filter(parent_category=this).order_by('my_category_name')

        for category in budget_categories:

            # When a hybrid is requested mash parent and child categories together returning key to child
            children = None
            if s == 'h':
                children = MyBudgetCategory.objects.filter(parent_category=category.pk).order_by('my_category_name')

            if children:
                for child in children:
                    record = {}
                    record['id'] = hashids.encode(child.pk)
                    record['my_category_name'] = category.my_category_name + ' > ' + child.my_category_name
                    record['core'] = 'no'
                    if child.category_perma_key:
                        record['core'] = 'yes'
                    data.append(record)

            else:
                record = {}
                record['id'] = hashids.encode(category.pk)
                record['my_category_name'] = category.my_category_name
                record['core'] = 'no'
                if category.category_perma_key:
                    record['core'] = 'yes'
                data.append(record)

        response_data['Result'] = 'OK'
        response_data['Records'] = data

    return JsonResponse(response_data)


@login_required
def ajax_create_category(request, pid):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_category_name_input(request.POST.get('my_category_name')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    this = hashids.decode(pid)[0]  # category's group pk
    cat_name = request.POST.get('my_category_name')

    # TODO: don't allow duplicate or similar categories

    group_obj = MyBudgetGroup.objects.get(pk=this)

    new_category = MyBudgetCategory()
    new_category.my_budget_group = group_obj
    new_category.my_category_name = cat_name
    new_category.save()

    record = {}
    record['id'] = hashids.encode(new_category.pk)
    record['my_category_name'] = new_category.my_category_name

    response_data['Result'] = 'OK'
    response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_update_category(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_id_input(request.POST.get('id')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)
    if not validate_category_name_input(request.POST.get('my_category_name')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    id_hashed = request.POST.get('id')  # category pk
    this = hashids.decode(id_hashed)[0]

    try:
        budget_category = MyBudgetCategory.objects.get(pk=this)
    except ObjectDoesNotExist:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Error getting budget category.'
        return JsonResponse(response_data)

    budget_category.my_category_name = request.POST.get('my_category_name')
    budget_category.save()

    record = {}
    record['my_category_name'] = request.POST.get('my_category_name')

    response_data['Result'] = 'OK'
    response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_delete_category(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_id_input(request.POST.get('id')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    id_hashed = request.POST.get('id')  # category pk
    this = hashids.decode(id_hashed)[0]

    try:
        budget_category = MyBudgetCategory.objects.get(pk=this)
    except ObjectDoesNotExist:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Error getting budget category.'
        return JsonResponse(response_data)

    if budget_category.category_perma_key:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Sorry, this is a core budget category used for comparisons and cannot be deleted.'
        return JsonResponse(response_data)

    budget_category.delete()
    response_data['Result'] = 'OK'

    return JsonResponse(response_data)


@login_required
def ajax_create_child_category(request, pid):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_category_name_input(request.POST.get('my_category_name')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    this = hashids.decode(pid)[0]  # category's parent pk

    cat_name = request.POST.get('my_category_name')

    # TODO: don't allow duplicate or similar categories; assuming use of google places will help

    parent = MyBudgetCategory.objects.get(pk=this)

    new_category = MyBudgetCategory()
    new_category.my_budget_group = parent.my_budget_group
    new_category.my_category_name = cat_name
    new_category.parent_category = parent
    new_category.save()

    record = {}
    record['id'] = hashids.encode(new_category.pk)
    record['my_category_name'] = new_category.my_category_name

    response_data['Result'] = 'OK'
    response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_list_budgets(request, pid):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:
        data = []

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        budget_records = MyBudget.objects.filter(category=hashids.decode(pid)[0]).order_by('-effective_date')
        for budget in budget_records:
            record = {}
            record['id'] = hashids.encode(budget.pk)
            record['amount'] = budget.amount
            record['annual_payment_month'] = budget.annual_payment_month
            record['note'] = budget.note
            record['effective_date'] = budget.effective_date
            data.append(record)

        response_data['Result'] = 'OK'
        response_data['Records'] = data

    return JsonResponse(response_data)


@login_required
def ajax_create_budget(request, pid):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_budget_inputs(request.POST.get('amount'),
                                  request.POST.get('annual_payment_month'),
                                  request.POST.get('note'),
                                  request.POST.get('effective_date')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid budget amount, annual month, note and/or effective date given.'
        return JsonResponse(response_data)

    # TODO: Capture invalid date; e.g. 2016-01-45

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    category_obj = MyBudgetCategory.objects.get(pk=hashids.decode(pid)[0])

    new_budget = MyBudget()
    new_budget.category = category_obj
    new_budget.amount = request.POST.get('amount')
    new_budget.annual_payment_month = request.POST.get('annual_payment_month')
    new_budget.note = request.POST.get('note')
    new_budget.effective_date = request.POST.get('effective_date')
    new_budget.save()

    record = {}
    record['id'] = hashids.encode(new_budget.pk)
    record['amount'] = new_budget.amount
    record['annual_payment_month'] = new_budget.annual_payment_month
    record['note'] = new_budget.note
    record['effective_date'] = new_budget.effective_date

    response_data['Result'] = 'OK'
    response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_change_budget(request, s):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_id_input(request.POST.get('id')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)
    if s == 'u':
        if not validate_budget_inputs(request.POST.get('amount'),
                                      request.POST.get('annual_payment_month'),
                                      request.POST.get('note'),
                                      request.POST.get('effective_date')):
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Invalid budget amount, annual month, note and/or effective date given.'
            return JsonResponse(response_data)

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

    try:
        budget = MyBudget.objects.get(pk=hashids.decode(request.POST.get('id'))[0])
    except ObjectDoesNotExist:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Error getting budget.'
        return JsonResponse(response_data)

    if s == 'd':
        budget.delete()
        response_data['Result'] = 'OK'
    else:
        budget.amount = request.POST.get('amount')
        budget.annual_payment_month = request.POST.get('annual_payment_month')
        budget.note = request.POST.get('note')
        budget.effective_date = datetime.datetime.strptime(request.POST.get('effective_date'), '%Y-%m-%d')
        budget.save()

        # Return only changed values since jTable supports it
        record = {}
        if budget.amount != request.POST.get('amount'):
            record['amount'] = request.POST.get('amount')
        if budget.annual_payment_month != request.POST.get('annual_payment_month'):
            record['annual_payment_month'] = request.POST.get('annual_payment_month')
        if budget.note != request.POST.get('note'):
            record['note'] = request.POST.get('note')
        if budget.effective_date != request.POST.get('effective_date'):
            record['effective_date'] = request.POST.get('effective_date')

        response_data['Result'] = 'OK'
        response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_budget_summary(request):
    """
    Create summary budget structure with amounts for display to Dandelion Diary subscriber.
    This is currently ajax to enable dynamic updating of amounts.

    Structure is:

    Field1 - Displays hierarchy structure of group, category, child-category
    Field2 - Amount for child category
    Field3 - Amount (or sum) for category
    Field4 - Sum for group, total budget
    Field5 - Effective date for category budgets

    :param request:
    :return:
    """

    response_data = {}

    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:

        data = []
        template = {'field1': '', 'field2': '', 'field3': '', 'field4': '', 'field5': ''}

        indent = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'

        budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')
        budget_total = 0

        for group in budget_groups:
            record = template.copy()
            record['field1'] = group.my_group_name
            data.append(record)

            group_total = 0

            categories = MyBudgetCategory.objects.filter(my_budget_group=group).filter(parent_category=None)\
                .order_by('my_category_name')

            for category in categories:

                category_budget = helper_get_category_budget_and_expenses(category, convert_annual=True)['budget']
                group_total += category_budget

                record = template.copy()
                record['field1'] = indent + category.my_category_name
                record['field2'] = category_budget
                data.append(record)

            budget_total += group_total

            record = template.copy()
            record['field1'] = 'Total for ' + group.my_group_name
            record['field3'] = group_total
            data.append(record)

        record = template.copy()
        record['field1'] = '<b>** Total monthly budget</b>'
        record['field3'] = '<b>' + str(budget_total) + '</b>'
        data.append(record)

        response_data['Result'] = 'OK'
        response_data['Records'] = data

    return JsonResponse(response_data)
