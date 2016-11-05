import datetime

from django.shortcuts import redirect, render, render_to_response, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_POST
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from hashids import Hashids

from household.helpers import  helper_get_me
from .helpers import helper_get_category_budget_and_expenses, helper_get_group_budget_and_expenses

from .models import MyBudgetGroup, MyBudgetCategory, MyBudget

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16


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

        context = {
            'page_title': 'Compare Dashboard',
            'url': 'compare:compare_dashboard',
        }

        return render(request, 'compare/compare_dashboard.html', context)


@login_required
def budgets_and_expenses(request):
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
            'page_title': 'Budgets + Expenses',
            'url': 'compare:budgets_expenses',
            'tabs': group_tabs,
            'keys': group_keys,
        }

        return render(request, 'compare/budgets_expenses.html', context)


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
def ajax_dash_budget(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        pass
    else:

        cols = [
            {'id': 'groups', 'label': 'Groups', 'type': 'string'},
            {'id': 'amount', 'label': 'Amount', 'type': 'number'}
        ]

        budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')
        rows = []

        for group in budget_groups:

            group_total = 0

            categories = MyBudgetCategory.objects.filter(my_budget_group=group).filter(parent_category=None)
            for category in categories:

                category_budget = helper_get_category_budget_and_expenses(category, fetch_expenses=False)['budget']
                group_total += category_budget

            row = {'c': [{'v': group.my_group_name}, {'v': int(group_total)}]}
            rows.append(row)

        response_data['cols'] = cols
        response_data['rows'] = rows

    return JsonResponse(response_data)


@login_required
def ajax_be_groups(request):
    """
    Budgets + Expenses: Show current or past budget and expense information

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

        budget_groups = MyBudgetGroup.objects.filter(household=me.get('household_key')).order_by('group_list_order')

        budget_total = 0
        expense_total = 0

        for group in budget_groups:

            record = {}
            record['group'] = group.my_group_name
            amounts = helper_get_group_budget_and_expenses(group)
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
def ajax_be_categories(request, pid):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:
        data = []

        budget_total = 0
        expense_total = 0

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        id=hashids.decode(pid)[0]

        budget_categories = MyBudgetCategory.objects.filter(my_budget_group=id).filter(parent_category=None)\
            .order_by('my_category_name')
        for category in budget_categories:

            record = {}
            record['my_category_name'] = category.my_category_name
            amounts = helper_get_category_budget_and_expenses(category, fetch_expenses=True)
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
    else:
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
    else:
        id_hashed = request.POST.get('id')
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        this=hashids.decode(id_hashed)[0]
        try:
            budget_group = MyBudgetGroup.objects.get(pk=this)
        except ObjectDoesNotExist:
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Error getting budget group.'
        else:
            if not budget_group.household.pk == me.get('household_key'):
                response_data['Result'] = 'ERROR'
                response_data['Message'] = 'Invalid request for budget group.'
            else:
                record = {}
                if not budget_group.my_group_name == request.POST.get('my_group_name'):
                    budget_group.my_group_name=request.POST.get('my_group_name')
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
    else:
        id_hashed = request.POST.get('id')
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        this=hashids.decode(id_hashed)[0]
        try:
            budget_group = MyBudgetGroup.objects.get(pk=this)
        except ObjectDoesNotExist:
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Error getting budget group.'
        else:
            if not budget_group.household.pk == me.get('household_key'):
                response_data['Result'] = 'ERROR'
                response_data['Message'] = 'Invalid request for budget group.'
            else:
                if budget_group.group_perma_key:
                    response_data['Result'] = 'ERROR'
                    response_data['Message'] = 'Sorry, this is a core budget group used for comparisons and ' \
                                               'cannot be deleted.'
                else:
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
        data = []
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        id=hashids.decode(pid)[0]

        # Get parent level categories for flags 'p'arent and 'h'ybrid
        if s == 'p' or s == 'h':
            budget_categories = MyBudgetCategory.objects.filter(my_budget_group=id).filter(parent_category=None)\
                .order_by('my_category_name')
        else:
            # Fetch 'c'hildren categories
            budget_categories = MyBudgetCategory.objects.filter(parent_category=id).order_by('my_category_name')

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
    else:
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        id=hashids.decode(pid)[0]  # category's group pk
        cat_name = request.POST.get('my_category_name')

        # to do: don't allow duplicate or similar categories; assuming looping in google places will help

        group_obj = MyBudgetGroup.objects.get(pk=id)
        # to do: validate group belongs to user

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
    else:
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        id_hashed = request.POST.get('id')  # category pk
        this=hashids.decode(id_hashed)[0]
        try:
            budget_category = MyBudgetCategory.objects.get(pk=this)
        except ObjectDoesNotExist:
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Error getting budget category.'
        else:
            record = {}
            budget_category.my_category_name = request.POST.get('my_category_name')
            budget_category.save()

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
    else:
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        id_hashed = request.POST.get('id')  # category pk
        this=hashids.decode(id_hashed)[0]
        try:
            budget_category = MyBudgetCategory.objects.get(pk=this)
        except ObjectDoesNotExist:
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Error getting budget category.'
        else:
            if budget_category.category_perma_key:
                response_data['Result'] = 'ERROR'
                response_data['Message'] = 'Sorry, this is a core budget category used for comparisons and ' \
                                               'cannot be deleted.'
            else:
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
    else:
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        id=hashids.decode(pid)[0]  # category's parent pk
        cat_name = request.POST.get('my_category_name')

        # to do: don't allow duplicate or similar categories; assuming looping in google places will help

        parent = MyBudgetCategory.objects.get(pk=id)
        # to do: is there further validation to be done for security purposes?

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
    else:
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        category_obj = MyBudgetCategory.objects.get(pk=hashids.decode(pid)[0])
        # to do: as security check, validate category belongs to user?

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
    else:

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        try:
            budget = MyBudget.objects.get(pk=hashids.decode(request.POST.get('id'))[0])
        except ObjectDoesNotExist:
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Error getting budget.'
        else:
            if s == 'd':
                pass
            else:
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

                budget.amount = request.POST.get('amount')
                budget.annual_payment_month = request.POST.get('annual_payment_month')
                budget.note = request.POST.get('note')
                budget.effective_date = datetime.datetime.strptime(request.POST.get('effective_date'),'%Y-%m-%d')
                budget.save()

                response_data['Result'] = 'OK'
                response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def ajax_budget_summary(request):
    """
    Create summary budget structure with amounts for display to Dande subscriber.
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

                category_budget = helper_get_category_budget_and_expenses(category)['budget']
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
