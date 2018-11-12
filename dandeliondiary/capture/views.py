import csv, datetime, random, decimal, operator, urllib

from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import modelformset_factory, fields


from google import get_nearby_places, byteify

from household.helpers import helper_get_me
from core.helpers import helpers_add_google_place
from .helpers import \
    helper_budget_categories, helper_budget_categories_places, \
    composite_category_name, \
    get_remaining_budget, \
    is_expense_place_type, \
    format_statement_date, \
    validate_filter_inputs, validate_expense_inputs, validate_expense_note_input, validate_id_input, \
    validate_paging_input

from core.models import GooglePlaceType
from compare.models import MyBudgetCategory
from capture.models import MyExpenseItem, MyReceipt, MyNoteTag, MyQuickAddCategoryAssociation

from .forms import NewExpenseForm, MyNoteTagForm, UploadFileForm, MyQuickAddCategoryAssociationForm

from hashids import Hashids

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16

GOOGLE_MOBILE_RADIUS = 130
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
            if split or form.cleaned_data.get('amount'):
                expense.note += ' Receipt {}.'.format(form.cleaned_data.get('amount_receipt'))
            if not form.cleaned_data.get('amount'):
                expense.amount = form.cleaned_data.get('amount_receipt')
            else:
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
                expense.note += ' Receipt {}.'.format(form.cleaned_data.get('amount_receipt'))
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

    tags = MyNoteTag.objects.filter(household=me.get('household_obj')).order_by('tag')
    default_tags = tags.filter(is_default=True)
    if default_tags:
        form.initial = {'note': ' '.join(t.tag for t in default_tags)}

    context = {
        'form': form,
        'page_title': 'Capture New Expense',
        'url': 'capture:new_expense',
        'location_message': location_message,
        'tags': tags,
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
def maintain_tags(request):
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        TagFormSet = modelformset_factory(
            MyNoteTag, form=MyNoteTagForm, fields=('tag', 'is_default', ), can_delete=True, extra=2)

        if request.method == 'POST':

            formset = TagFormSet(request.POST)
            if formset.is_valid():

                for ndx, form in enumerate(formset):
                    if form.is_valid() and not form.empty_permitted:

                        if ndx in formset._deleted_form_indexes:
                            messages.warning(
                                request,
                                "'{}' has been deleted.".format(form.cleaned_data.get('tag'))
                            )
                            formset.save()

                        else:

                            if form.changed_data:
                                form.save()
                                messages.success(request, 'Your information has been saved.')

                    else:

                        if form.changed_data:

                            try:
                                new_tag = form.save(commit=False)

                            except ValueError:
                                pass  # Error is raised when tag is empty but delete was selected

                            else:
                                new_tag.household = me.get('household_obj')
                                try:
                                    new_tag.save()

                                except IntegrityError:
                                    messages.warning(
                                        request,
                                        "'{}' was not saved because it is a duplicate tag."
                                            .format(form.cleaned_data.get('tag'))
                                    )

                                else:
                                    messages.success(request, "'{}' has been added."
                                                     .format(form.cleaned_data.get('tag')))

                return redirect('capture:maintain_tags')

            else:
                messages.warning(request, "Please fix the error(s) noted below.")

        else:

            formset = TagFormSet(queryset=MyNoteTag.objects.filter(household=me.get('household_obj')).order_by('tag'))

        context = {
            'formset': formset,
            'page_title': 'Maintain Note Tags',
            'url': 'capture:maintain_tags',
        }

    return render(request, 'capture/tags.html', context)


@login_required
def maintain_payee_associations(request):
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        PayeeAssociationsFormSet = modelformset_factory(
            MyQuickAddCategoryAssociation, form=MyQuickAddCategoryAssociationForm,
            fields=('payee_contains', 'category', ), can_delete=True, extra=2)

        if request.method == 'POST':

            formset = PayeeAssociationsFormSet(request.POST)
            if formset.is_valid():

                for ndx, form in enumerate(formset):
                    if form.is_valid() and not form.empty_permitted:

                        if ndx in formset._deleted_form_indexes:
                            messages.warning(
                                request,
                                "'{}' has been deleted.".format(form.cleaned_data.get('payee_contains'))
                            )
                            formset.save()

                        else:

                            if form.changed_data:
                                form.save()
                                messages.success(request, 'Your information has been saved.')

                    else:

                        if form.changed_data:

                            try:
                                new_association = form.save(commit=False)

                            except ValueError:
                                pass  # Error is raised when tag is empty but delete was selected

                            else:
                                new_association.household = me.get('household_obj')
                                try:
                                    new_association.save()

                                except IntegrityError:
                                    messages.warning(
                                        request,
                                        "'{}' was not saved because it is a duplicate."
                                            .format(form.cleaned_data.get('payee_contains'))
                                    )

                                else:
                                    messages.success(request, "'{}' has been added."
                                                     .format(form.cleaned_data.get('payee_contains')))

                return redirect('capture:maintain_payee_associations')

            else:
                messages.warning(request, "Please fix the error(s) noted below.")

        else:

            formset = PayeeAssociationsFormSet(queryset=MyQuickAddCategoryAssociation.objects
                                               .filter(household=me.get('household_obj')).order_by('payee_contains'))

        context = {
            'formset': formset,
            'page_title': 'Maintain Payee and Expense Associations',
            'url': 'capture:maintain_payee_associations',
        }

    return render(request, 'capture/payee_contains.html', context)


@login_required
def export_expenses_to_csv(request):

    from_date = request.GET.get('frDate', '')
    if from_date:
        try:
            valid_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
        except ValueError:
            from_date = ''
    if not from_date:
        from_date = '1900-01-01'

    to_date = request.GET.get('toDate', '')
    if to_date:
        try:
            valid_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
        except ValueError:
            to_date = ''
    if not to_date:
        to_date = datetime.datetime.today().strftime('%Y-%m-%d')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Expense Date', 'Group', 'Parent Category', 'Category', 'Amount', 'Who', 'Note'])

    expenses = MyExpenseItem.objects.filter(expense_date__range=[from_date, to_date]).order_by("expense_date") \
        .values_list('expense_date',
                     'category__my_budget_group__my_group_name',
                     'category__parent_category__my_category_name',
                     'category__my_category_name',
                     'amount',
                     'who__user__username',
                     'note')

    # Create buckets for tags that support reconciliation of expenses
    amber_pd = 0
    scot_pd = 0
    amber_not_shared = 0
    scot_not_shared = 0
    amber_split_50_50 = 0
    scot_split_50_50 = 0
    amber_iou = 0
    scot_iou = 0
    total_expenses = 0

    # Write expenses to the CSV file, tally amounts as you go
    for expense in expenses:

        writer.writerow(expense)

        # Tally items by tag
        if 'Amber pd.' in expense[6]:
            amber_pd += expense[4]
            if 'Not shared.' in expense[6]:
                amber_not_shared += expense[4]
            if '50-50 split.' in expense[6]:
                amber_split_50_50 += expense[4]
            if 'Scot IOU.' in expense[6]:
                scot_iou += expense[4]

        if 'Scot pd.' in expense[6]:
            scot_pd += expense[4]
            if 'Not shared.' in expense[6]:
                scot_not_shared += expense[4]
            if '50-50 split.' in expense[6]:
                scot_split_50_50 += expense[4]
            if 'Amber IOU.' in expense[6]:
                amber_iou += expense[4]

        total_expenses += expense[4]

    # Create and write reconciliation to the file
    writer.writerow(['Count:', len(expenses), '', '', '', '', ''])
    writer.writerow(['Total expenses:', total_expenses, '', '', '', '', ''])
    if amber_pd or scot_pd:
        check_total = amber_pd + scot_pd
        check_msg = 'Error'
        if check_total == total_expenses:
            check_msg = 'OK'
        writer.writerow(['', '', '', '', '', '', ''])
        writer.writerow(['a', 'Amber pd.', amber_pd, '', '', '', ''])
        writer.writerow(['b', 'Scot pd.', scot_pd, '', '', '', ''])
        writer.writerow(['', 'Check total:', check_total, check_msg, '', '', ''])
        writer.writerow(['', '', '', '', '', '', ''])
        writer.writerow(['c', 'Amber, not shared:', amber_not_shared, '', '', '', ''])
        writer.writerow(['d', 'Amber, 50-50 split:', amber_split_50_50, '', '', '', ''])
        writer.writerow(['e', 'Amber, IOU:', amber_iou, '', '', '', ''])
        writer.writerow(['', '', '', '', '', '', ''])
        writer.writerow(['f', 'Scot, not shared:', scot_not_shared, '', '', '', ''])
        writer.writerow(['g', 'Scot, 50-50 split', scot_split_50_50, '', '', '', ''])
        writer.writerow(['h', 'Scot, IOU:', scot_iou, '', '', '', ''])
        writer.writerow(['', '', '', '', '', '', ''])

        baseline = amber_pd - (amber_not_shared + amber_split_50_50 + scot_iou)
        writer.writerow(['i', 'Baseline:', '', baseline, 'a - (c + d + h)', '', ''])

        amount = baseline * decimal.Decimal(.15)
        reimbursement = round(decimal.Decimal(amount), 2)
        writer.writerow(['j', 'Baseline reimbursement:', '', reimbursement, 'i * .15', '', ''])
        writer.writerow(['', '', '', '', '', '', ''])

        amount = amber_split_50_50 * decimal.Decimal(.5)
        reimbursement += round(decimal.Decimal(amount), 2)
        writer.writerow(['k', 'Plus 50-50 split:', round(decimal.Decimal(amount), 2), reimbursement, 'j + (d * .5)', '', ''])

        reimbursement += round(decimal.Decimal(scot_iou), 2)
        writer.writerow(['l', 'Plus Scot IOU:', scot_iou, reimbursement, 'k + h', '', ''])

        amount = (scot_pd - (scot_not_shared + scot_split_50_50 + amber_iou)) * decimal.Decimal(.85)
        reimbursement -= round(decimal.Decimal(amount), 2)
        writer.writerow(['m', 'Less Scot pd:', round(decimal.Decimal(amount), 2), reimbursement, '(b - (f + g + e)) * .85', '', ''])

        amount = scot_split_50_50 * decimal.Decimal(.5)
        reimbursement -= round(decimal.Decimal(amount), 2)
        writer.writerow(['n', 'Less 50-50 split:', round(decimal.Decimal(amount), 2), reimbursement, 'm - (g * .5)', '', ''])

        reimbursement -= round(decimal.Decimal(amber_iou), 2)
        writer.writerow(['o', 'Less Amber IOU:', amber_iou, reimbursement, 'n - e', '', ''])

        writer.writerow(['', '', '', '', '', '', ''])
        if reimbursement < 0:
            reimbursement_message = 'Amber to reimburse Scot:'
        else:
            reimbursement_message = 'Scot to reimburse Amber:'
        writer.writerow(['', reimbursement_message, reimbursement, '', '', '', ''])

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

        if filters['ckReconciled'] == 'true':
            expenses = expenses.filter(reconciled=False)
        else:
            pass

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
        record['reconciled'] = expense.reconciled

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
        reconciled = request.POST.get('reconciled', 'false')
        if not expense.reconciled == reconciled:
            expense.reconciled = reconciled.title()
            record['reconciled'] = reconciled
        expense.save()
        response_data['Result'] = 'OK'
        response_data['Record'] = record

    return JsonResponse(response_data)


@login_required
def reconcile_expenses(request):

    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')

    step = 1
    headings = []
    statement_expenses_reconciled = []
    statement_expenses_not_reconciled = []

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():

            period_end_date = datetime.datetime.strptime(form.cleaned_data['period'], '%Y-%m-%d')
            period_start_date = period_end_date.replace(day=1)
            dd_period_expenses = MyExpenseItem.objects.filter(expense_date__gte=period_start_date) \
                .filter(expense_date__lte=period_end_date)

            statement_expenses = csv.DictReader(form.cleaned_data['file'])

            can_process_checked = False
            error = False
            date_key = None
            amount_key = None

            for item in statement_expenses:

                # First time only, validate we can find a date and amount field.
                if not can_process_checked:
                    try:
                        date_key = next(k for k, v in item.items() if 'Date' in k)
                    except:
                        messages.warning(request, "Could not find Date in CSV file.")
                        error = True
                        break

                    try:
                        amount_key = next(k for k, v in item.items() if 'Amount' in k)
                    except:
                        messages.warning(request, "Could not find Amount in CSV file.")
                        error = True
                        break

                    headings.append(date_key)
                    headings.append(amount_key)
                    for key, v in item.items():
                        if key not in headings:
                            headings.append(key)
                    headings.append('Info Message')
                    headings.append('Quick Add')

                    can_process_checked = True

                # Validate and convert statement date to date object
                result = format_statement_date(item[date_key], form.cleaned_data['date_format'])
                if not result[0] == 'OK':
                    messages.warning(request, "CSV file contains one or more invalid dates or incorrect format was "
                                              "selected.")
                    error = True
                    break
                else:
                    item_date = result[1]

                if item_date.year == period_end_date.year and item_date.month == period_end_date.month:

                    expenses = None
                    match_limit = 0
                    info_msg = ''

                    # First look for items where statement amount matches an expense amount in DandelionDiary.
                    dd_matches_set_a = dd_period_expenses.filter(amount=abs(decimal.Decimal(item[amount_key])))
                    if len(dd_matches_set_a) > 0:  # One or more expense amounts in DandelionDiary match statement
                        if len(dd_matches_set_a) == 1:  # If only one matches, we're good to go
                            expenses = dd_matches_set_a
                        else:
                            match_limit = 1

                    # If no match on amount, try based on receipt amount recorded in note tag.
                    if not expenses and not match_limit:
                        dd_matches_set_a = dd_period_expenses\
                            .filter(note__icontains=abs(decimal.Decimal(item[amount_key])))
                        if len(dd_matches_set_a) > 0: # One or more expense notes in DandelionDiary match statement
                            if len(dd_matches_set_a) == 1:
                                expenses = dd_matches_set_a
                            else:
                                if len(dd_matches_set_a) < 3:  # If split match, we're good to go
                                    if dd_matches_set_a[0].expense_date == dd_matches_set_a[1].expense_date:
                                        expenses = dd_matches_set_a
                                    else:
                                        match_limit = 1  # Not a split; try to match based on date
                                else:
                                    match_limit = 2  # Try to narrow the mayhem down by date

                    # If match limit, expenses were found but need to be narrowed by date.
                    if not expenses and match_limit:
                        early_date = item_date - datetime.timedelta(days=2)
                        dd_matches_set_b = dd_matches_set_a.filter(expense_date__gte=early_date)\
                            .filter(expense_date__lte=item_date)
                        if len(dd_matches_set_b) > 0:
                            if len(dd_matches_set_b) <= match_limit:
                                expenses = dd_matches_set_b
                            else:
                                info_msg = 'This item has an amount matching one or more expenses occurring ' \
                                            'within a couple days of each other. '
                        else:
                            info_msg = 'This item has an amount matching one or more expenses, but the expense ' \
                                        'dates recorded do not occur within a 2 day period of the statement date.'

                    if expenses:

                        for expense in expenses:
                            reconciled_item = {}
                            reconciled_item['expense_date'] = expense.expense_date
                            category = MyBudgetCategory.objects.get(pk=expense.category.pk)
                            reconciled_item['category'] = category.my_category_name
                            reconciled_item['amount'] = expense.amount
                            reconciled_item['note'] = expense.note

                            if expense.reconciled is False:
                                expense.reconciled = True
                                expense.save()

                                reconciled_item['tag'] = ''

                            else:
                                reconciled_item['tag'] = '*'

                            statement_expenses_reconciled.append(reconciled_item)

                    else:

                        item[date_key] = item_date.strftime('%Y-%m-%d')
                        item[amount_key] = abs(decimal.Decimal(item[amount_key]))

                        item['Info Message'] = info_msg
                        if info_msg:
                            item['Quick Add'] = ''
                        else:
                            item['Quick Add'] = 'insert button'
                        item.update()

                        ordered_item = []
                        for heading in headings:
                            ordered_item.append(item[heading])

                        statement_expenses_not_reconciled.append(ordered_item)

            # return HttpResponseRedirect('/success/url/')

            if not error:
                step = 3

    else:
        form = UploadFileForm()

    category_choices = helper_budget_categories(me.get('household_key'), top_load=True)
    category = fields.ChoiceField(choices=category_choices)
    field_name = 'modalCategory'
    category_html = category.widget.render(field_name, 0)

    tags = MyNoteTag.objects.filter(household=me.get('household_obj')).order_by('tag')

    context = {
        'page_title': 'Reconcile Expenses',
        'url': 'capture:reconcile_expenses',
        'step': step,
        'form': form,
        'expenses_reconciled': sorted(statement_expenses_reconciled, key=lambda k: k['expense_date']),
        'expenses_not_reconciled': sorted(statement_expenses_not_reconciled, key=operator.itemgetter(0)),
        'headings': headings,
        'category': category_html,
        'tags': tags,
    }

    return render(request, 'capture/reconcile_expenses.html', context)


@login_required
def ajax_expense_quick_add(request):

    response_data = {}

    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        response_data['status'] = 'ERROR'
        response_data['message'] = 'Invalid request.'
        return JsonResponse(response_data)

    try:
        date = datetime.datetime.strptime(request.GET['dt'], '%Y-%m-%d')
    except:
        response_data['status'] = 'ERROR'
        response_data['message'] = 'Invalid date.'
        return JsonResponse(response_data)

    try:
        amount = decimal.Decimal(request.GET['amt'])
    except:
        response_data['status'] = 'ERROR'
        response_data['message'] = 'Invalid amount.'
        return JsonResponse(response_data)

    try:
        category_id = int(request.GET['cat'])
    except:
        response_data['status'] = 'ERROR'
        response_data['message'] = 'Invalid category.'
        return JsonResponse(response_data)

    try:
        note = urllib.unquote(request.GET['nt'])
    except:
        response_data['status'] = 'ERROR'
        response_data['message'] = 'Invalid note.'
        return JsonResponse(response_data)
    else:
        valid_note = validate_expense_note_input(note)
        if not valid_note:
            response_data['status'] = 'ERROR'
            response_data['message'] = 'Invalid note.'
            return JsonResponse(response_data)

    category = MyBudgetCategory.objects.get(pk=category_id)

    expense = MyExpenseItem()
    expense.expense_date = date
    expense.amount = amount
    expense.category = category
    expense.note = note
    expense.household = me.get('household_obj')
    expense.who = me.get('account_obj')
    expense.reconciled = True
    try:
        expense.save()
    except:
        response_data['status'] = 'ERROR'
        response_data['message'] = 'Save failed.'
        return JsonResponse(response_data)

    response_data['status'] = 'OK'
    response_data['message'] = 'Expense added.'
    return JsonResponse(response_data)
