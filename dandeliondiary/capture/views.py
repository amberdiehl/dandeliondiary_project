from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist


from google import get_nearby_places, byteify

from household.helpers import helper_get_me
from .helpers import helper_budget_categories, get_remaining_budget

from .forms import NewExpenseForm
from compare.models import MyBudgetCategory
from .models import MyExpenseItem

from hashids import Hashids

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16

# from uscampgrounds.models import *
# camps = Campground.objects.all().distance(origin).order_by('distance')


# Capture a new expense item
@login_required
def new_expense(request):
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        location_message = None
        geo = None

        if request.method == 'POST':

            form = NewExpenseForm(request.POST)

            if form.is_valid():

                # Create expense record
                expense = MyExpenseItem()
                expense.note = form.cleaned_data.get('note')
                expense.amount = form.cleaned_data.get('amount')
                expense.household = me.get('household_obj')
                expense.who = me.get('account_obj')
                category = int(form.cleaned_data.get('choose_category_place'))
                if category == 0:
                    category = int(form.cleaned_data.get('choose_category'))
                expense.category = MyBudgetCategory.objects.get(pk=category)
                #expense.google_place = ''
                expense.save()
                messages.success(request, 'Your information has been saved.')

                remaining_budget = get_remaining_budget(category)
                message = 'You have {} left in your budget.'.format(remaining_budget)
                if remaining_budget > 0:
                    messages.success(request, message)
                else:
                    messages.error(request, message)

                form = NewExpenseForm()

            else:

                messages.warning(request, "Please fix the errors noted below.")

        else:

            form = NewExpenseForm()

        # Attempt to get geolocation information to preselect categories
        position = ()
        if request.GET.get('lat') and request.GET.get('lon'):
            position = (request.GET.get('lat'),request.GET.get('lon'))
            geo = '?lat={}&lon={}'.format(request.GET.get('lat'),request.GET.get('lon'))

        places = ''  # if using for choice, change to []
        place_types = []
        if position:
            nearby_json = byteify(get_nearby_places(position, 75))
            for place in nearby_json['results']:
                # item = (place['place_id'], place['name']) <-- use for choice in the future
                places += place['name'] + ' '
                place_types.append(place['types'])  # this is an array of arrays
                # places.sort(key=lambda items: items[1])

        location_message = ('warning', 'Geolocation failed; category selection assistance unavailable.')
        if places:
            location_message = ('success','Geolocation information used for category selection assistance.')

        category_choices = helper_budget_categories(me.get('household_key'), place_types)
        form.fields['choose_category_place'].choices = category_choices[0]
        form.fields['choose_category'].choices = category_choices[1]

        context = {
            'form': form,
            'places': places,
            'page_title': 'Capture New Expense',
            'url': 'capture:new_expense',
            'geo': geo,
            'location_message': location_message,
        }

        return render(request, 'capture/new_expense.html', context)


@login_required
def explore_expenses(request):
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        context = {
         'page_title': 'Explore Expenses',
         'url': 'capture:explore_expenses',
        }

    return render(request, 'capture/explore_expenses.html', context)


@login_required
def ajax_list_expenses(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:
        data = []

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        expenses = MyExpenseItem.objects.filter(household=me.get('household_key')).order_by('-expense_date')
        for expense in expenses:
            record = {}
            record['id'] = hashids.encode(expense.pk)
            record['expense_date'] = expense.expense_date
            record['amount'] = expense.amount
            expense_category = MyBudgetCategory.objects.get(pk=expense.category.pk)
            record['category'] = expense_category.my_category_name
            record['note'] = expense.note
            data.append(record)

        response_data['Result'] = 'OK'
        response_data['Records'] = data
        response_data['TotalRecordCount'] = len(record)

    return JsonResponse(response_data)


@login_required
def ajax_change_expense(request, s):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
    else:
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        id_hashed = request.POST.get('id')
        this=hashids.decode(id_hashed)[0]
        try:
            expense = MyExpenseItem.objects.get(pk=this)
        except ObjectDoesNotExist:
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Error getting expense.'
        else:
            if not expense.household.pk == me.get('household_key'):
                response_data['Result'] = 'ERROR'
                response_data['Message'] = 'Invalid request for expense.'
            else:
                if s == 'd':
                    expense.delete()
                    response_data['Result'] = 'OK'
                    response_data['Record'] = ''
                else:
                    record = {}
                    if not expense.expense_date == request.POST.get('expense_date'):
                        expense.expense_date=request.POST.get('expense_date')
                        record['expense_date'] = request.POST.get('expense_date')
                    if not expense.amount == request.POST.get('amount'):
                        expense.amount = request.POST.get('amount')
                        record['amount'] = request.POST.get('amount')
                    if not expense.note == request.POST.get('note'):
                        expense.note = request.POST.get('note')
                        record['note'] = request.POST.get('note')
                    expense.save()
                    response_data['Result'] = 'OK'
                    response_data['Record'] = record

    return JsonResponse(response_data)
