import csv, datetime, random

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.auth.models import User


from google import get_nearby_places, byteify

from household.helpers import helper_get_me
from core.helpers import helpers_add_google_place
from .helpers import \
    helper_budget_categories, helper_budget_categories_places, \
    composite_category_name, \
    get_remaining_budget, \
    is_expense_place_type, \
    validate_filter_inputs, validate_expense_inputs, validate_id_input, validate_paging_input

from core.models import GooglePlaceType
from compare.models import MyBudgetCategory
from .models import MyExpenseItem, MyReceipt

from .forms import NewExpenseForm

from hashids import Hashids

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16

GOOGLE_MOBILE_RADIUS = 35
GOOGLE_DESKTOP_RADIUS = 2500

MOBILE_DEVICES = ['sony', 'symbian', 'nokia', 'samsung', 'mobile', 'windows ce', 'epoc', 'opera mini', 'nitro', 'j2me',
                  'midp-', 'cldc-', 'netfront', 'mot', 'up.browser', 'up.link', 'audiovox', 'blackberry', 'ericsson,',
                  'panasonic', 'philips', 'sanyo', 'sharp', 'sie-', 'portalmmm',  'blazer',  'avantgo',  'danger',
                  'palm', 'series60', 'palmsource', 'pocketpc', 'smartphone', 'rover', 'ipaq', 'au-mic,', 'alcatel',
                  'ericy', 'up.link', 'docomo', 'vodafone/', 'wap1.', 'wap2.', 'plucker', '480x640', 'sec', 'fennec',
                  'android', 'google wireless transcoder', 'nintendo', 'webtv', 'playstation',
                  ]


# Capture a new expense item
@login_required
def new_expense(request):
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')

    location_message = ''

    if request.method == 'POST':

        form = NewExpenseForm(request.POST, request.FILES)

        if form.is_valid():

            split = form.cleaned_data.get('split')

            # Create expense record
            expense = MyExpenseItem()
            expense.note = form.cleaned_data.get('note')
            expense.amount = form.cleaned_data.get('amount')
            if split:
                adjustment_amount = form.cleaned_data.get('amount_split')
                expense.amount -= adjustment_amount
            expense.household = me.get('household_obj')
            expense.who = me.get('account_obj')
            category = int(form.cleaned_data.get('choose_category'))
            expense.category = MyBudgetCategory.objects.get(pk=category)
            place = form.cleaned_data.get('choose_place').split('^')
            if len(place) > 1:
                expense.google_place = helpers_add_google_place(place[0], place[1], place[2], place[3])
            if not form.cleaned_data.get('expense_date'):
                form.cleaned_data['expense_date'] = datetime.datetime.today().date()
            expense.expense_date = form.cleaned_data.get('expense_date')
            expense.save()

            remaining_budget = get_remaining_budget(category, expense.expense_date)
            message = 'Got it! You have {} left in your {} budget.'\
                .format(remaining_budget, expense.category.my_category_name.lower())
            if remaining_budget > 0:
                messages.success(request, message)
            else:
                messages.error(request, message)

            receipt_file = form.cleaned_data.get('receipt')
            if receipt_file:

                hashids = Hashids(salt=settings.MEDIA_HASH_SALT, min_length=settings.MEDIA_HASH_MIN_LENGTH)
                to_hash1 = hashids.encode(random.randint(1, 999999999999))
                to_hash2 = hashids.encode(expense.pk)
                file_name = '{}{}.{}'.format(to_hash1, to_hash2, receipt_file.content_type.split('/')[1])

                receipt = MyReceipt()
                receipt.expense_item = expense
                receipt.original_name = receipt_file.name
                receipt.receipt = receipt_file
                receipt.receipt.name = file_name
                receipt.save()

            if split:
                expense = MyExpenseItem()
                expense.note = form.cleaned_data.get('note_split')
                expense.amount = form.cleaned_data.get('amount_split')
                expense.household = me.get('household_obj')
                expense.who = me.get('account_obj')
                category_split = int(form.cleaned_data.get('choose_category_split'))
                expense.category = MyBudgetCategory.objects.get(pk=category_split)
                if not form.cleaned_data.get('expense_date'):
                    form.cleaned_data['expense_date'] = datetime.datetime.today().date()
                expense.expense_date = form.cleaned_data.get('expense_date')
                expense.save()

                remaining_budget = get_remaining_budget(category_split, expense.expense_date)
                message = 'Got it! You have {} left in your {} budget.'\
                    .format(remaining_budget, expense.category.my_category_name.lower())
                if remaining_budget > 0:
                    messages.success(request, message)
                else:
                    messages.error(request, message)

            form = NewExpenseForm()

        else:

            messages.warning(request, "Please fix the errors noted below.")

    else:

        form = NewExpenseForm()
        location_message = ('error', 'Getting geo location information.')

    category_choices = helper_budget_categories(me.get('household_key'), top_load=True)
    form.fields['choose_category'].choices = category_choices
    form.fields['choose_category_split'].choices = category_choices

    context = {
        'form': form,
        'page_title': 'Capture New Expense',
        'url': 'capture:new_expense',
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
def export_expenses_to_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Expense Date', 'Group', 'Parent Category', 'Category', 'Amount', 'Who', 'Note'])

    expenses = MyExpenseItem.objects.all()\
        .values_list('expense_date',
                     'category__my_budget_group__my_group_name',
                     'category__parent_category__my_category_name',
                     'category__my_category_name',
                     'amount',
                     'who__user__username',
                     'note')
    for expense in expenses:
        writer.writerow(expense)

    return response


@login_required
def ajax_categories_by_place(request, lat, lon):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Status'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    if any(device in request.environ['HTTP_USER_AGENT'].lower() for device in MOBILE_DEVICES):
        radius = GOOGLE_MOBILE_RADIUS
    else:
        radius = GOOGLE_DESKTOP_RADIUS

    position = (lat, lon)
    places = []  # collect places to show for user selection
    place_types = []  # collect place types to enable expense category chooser based on location

    try:
        nearby_json = byteify(get_nearby_places(position, radius))
        if nearby_json['status'] == 'OK':

            # Collect places for place chooser
            types = GooglePlaceType.objects.all().values_list('type', flat=True)
            for place in nearby_json['results']:
                if is_expense_place_type(place['types'], types):  # only show places where type is valid
                    item = "{}^{}^{}^{}".format(place['place_id'], place['name'], place['geometry']['location']['lat'],
                            place['geometry']['location']['lng'])
                    places += (item, place['name']),
                    place_types.append(place['types'])  # this is an array of arrays
            places.sort(key=lambda items: items[1])

            response_data['Status'] = 'OK'
            response_data['places'] = places
            response_data['category_places'] = helper_budget_categories_places(me.get('household_key'), place_types)

        else:

            response_data['Status'] = 'ERROR'
            response_data['Message'] = '{}: {}'.format(nearby_json['status'], nearby_json['error_message'])

    except Exception as err:

        response_data['Status'] = 'ERROR'
        response_data['Message'] = 'ERROR: {}'.format(err)

    return JsonResponse(response_data)


@login_required
def ajax_list_expenses(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    if not validate_paging_input(request.GET['jtStartIndex']) or not validate_paging_input(request.GET['jtPageSize']):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)

    data = []

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

    start_index = int(request.GET['jtStartIndex'])
    page_size = int(request.GET['jtPageSize'])

    # Get all recorded expenses--this may need to be limited in the future to past three years, or in kind
    expenses = MyExpenseItem.objects.filter(household=me.get('household_key')).order_by('-expense_date')

    # Filter, if specified by user; for now this acts as an 'AND'.
    if request.POST:

        error, message = validate_filter_inputs(dict(request.POST))
        if error:
            response_data['Result'] = 'ERROR'
            response_data['Message'] = message
            return JsonResponse(response_data)

        filters = request.POST

        if filters['frDate']:
            if filters['toDate']:
                expenses = expenses.filter(expense_date__gte=filters['frDate'])\
                    .filter(expense_date__lte=filters['toDate'])
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

    # Handle pagination
    if (start_index + page_size) > record_count:
        expense_page = expenses[start_index:None]
    else:
        expense_page = expenses[start_index:start_index + page_size]

    for expense in expense_page:
        record = {}
        record['id'] = hashids.encode(expense.pk)
        record['expense_date'] = expense.expense_date
        record['amount'] = expense.amount
        c = MyBudgetCategory.objects.get(pk=expense.category.pk)
        record['category'] = composite_category_name(c.my_category_name, c.parent_category, c.my_budget_group)
        record['note'] = expense.note

        try:
            receipt = MyReceipt.objects.get(expense_item=expense)
        except ObjectDoesNotExist:
            record['receipt'] = 'none'
        else:
            record['receipt'] = receipt.receipt.name

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
        return JsonResponse(response_data)

    # Validate content type of data submitted before continuing
    if not validate_id_input(request.POST.get('id')):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request.'
        return JsonResponse(response_data)
    if not s == 'd':
        if not validate_expense_inputs(request.POST.get('expense_date'), request.POST.get('amount'), request.POST.get('note')):
            response_data['Result'] = 'ERROR'
            response_data['Message'] = 'Special characters in your note must be limited to: . , () + - / and =. ' \
                                       'Amount may not contain the $ symbol.'
            return JsonResponse(response_data)

    hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
    id_hashed = request.POST.get('id')
    this = hashids.decode(id_hashed)[0]

    try:
        expense = MyExpenseItem.objects.get(pk=this)
    except ObjectDoesNotExist:
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Error getting expense.'
        return JsonResponse(response_data)

    if not expense.household.pk == me.get('household_key'):
        response_data['Result'] = 'ERROR'
        response_data['Message'] = 'Invalid request for expense.'
        return JsonResponse(response_data)

    if s == 'd':
        expense.delete()
        response_data['Result'] = 'OK'
    else:
        record = {}
        if not expense.expense_date == request.POST.get('expense_date'):
            expense.expense_date = request.POST.get('expense_date')
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
