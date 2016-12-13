import datetime
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from PIL import Image

from google import get_nearby_places, byteify

from household.helpers import helper_get_me
from core.helpers import helpers_add_google_place
from .helpers import helper_budget_categories, get_remaining_budget, is_expense_place_type

from core.models import GooglePlaceType
from compare.models import MyBudgetCategory
from .models import MyExpenseItem, MyReceipt

from .forms import NewExpenseForm

from hashids import Hashids

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16

GOOGLE_LOCATION_RADIUS = 35
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

        geo = None

        if request.method == 'POST':

            form = NewExpenseForm(request.POST, request.FILES)

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
                place = form.cleaned_data.get('choose_place').replace('(','').replace(')','').replace("'",'').split(',')
                if len(place) > 1:
                    expense.google_place = helpers_add_google_place(place[0], place[1], place[2], place[3])
                if not form.cleaned_data.get('expense_date'):
                    form.cleaned_data['expense_date'] = datetime.datetime.today().date()
                expense.expense_date = form.cleaned_data.get('expense_date')
                expense.save()

                receipt_file = form.cleaned_data.get('receipt')
                if receipt_file:
                    receipt = MyReceipt()
                    receipt.expense_item = expense
                    receipt.original_name = receipt_file.name
                    receipt.receipt = receipt_file
                    receipt.receipt.name = '{}-{}.{}'\
                        .format(me.get('household_key'), expense.pk, receipt_file.content_type.split('/')[1])
                    receipt.save()

                messages.success(request, 'Your information has been saved.')

                remaining_budget = get_remaining_budget(category, expense.expense_date)
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
            location_message = ('success','Geolocation used for expense category assistance.')
        else:
            location_message = ('warning', 'Geolocation failed; category assistance unavailable.')

        places = [(0, '------'),]  # collect places to show for user selection
        place_types = []  # collect place types to enable expense category chooser based on location
        places_error = '' # show error in case cause is change in IP address
        if position:
            try:
                nearby_json = byteify(get_nearby_places(position, GOOGLE_LOCATION_RADIUS))
                if nearby_json['status'] == 'OK':
                    types = GooglePlaceType.objects.all().values_list('type', flat=True)
                    for place in nearby_json['results']:
                        if is_expense_place_type(place['types'], types): # only show places where type is valid
                            item = (place['place_id'], place['name'], place['geometry']['location']['lat'],
                                    place['geometry']['location']['lng'])
                            places += (item, place['name']),
                            place_types.append(place['types'])  # this is an array of arrays
                    places.sort(key=lambda items: items[1])
                else:
                    places_error = 'status: {} error message: {}'.format(nearby_json['status'],
                                                                         nearby_json['error_message'])
            except Exception as err:
                pass

        category_choices = helper_budget_categories(me.get('household_key'), place_types)
        form.fields['choose_category_place'].choices = category_choices[0]
        form.fields['choose_category'].choices = category_choices[1]
        form.fields['choose_place'].choices = places

        context = {
            'form': form,
            'places': len(places),
            'places_error': places_error,
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

        start_index = int(request.GET['jtStartIndex'])
        page_size = int(request.GET['jtPageSize'])

        # Get all recorded expenses--this may need to be limited in the future to past three years, or in kind
        expenses = MyExpenseItem.objects.filter(household=me.get('household_key')).order_by('-expense_date')

        # Filter, if specified by user; for now this acts as an 'AND'.
        if request.POST:
            filters = request.POST
            if filters['frDate']:
                if filters['toDate']:
                    expenses = expenses.filter(expense_date__gte=filters['frDate']).filter(expense_date__lte=filters['toDate'])
                else:
                    expenses = expenses.filter(expense_date=filters['frDate'])

            if filters['frAmount']:
                from_amount = float(filters['frAmount'])
                if filters['toAmount']:
                    to_amount = float(filters['toAmount'])
                    expenses = expenses.filter(amount__gte=from_amount).filter(amount__lte=to_amount)
                else:
                    expenses = expenses.filter(amount=from_amount)

            if filters['inCategory']:
                expenses = expenses.filter(category__my_category_name__icontains=filters['inCategory'])

            if filters['inNote']:
                expenses = expenses.filter(note__icontains=filters['inNote'])

        record_count = len(expenses)

        if (start_index + page_size) > record_count:
            expenses = expenses[start_index:None]
        else:
            expenses = expenses[start_index:page_size]

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
        response_data['TotalRecordCount'] = record_count

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
