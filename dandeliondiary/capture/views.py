from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, render_to_response, redirect
from django.http import HttpResponseRedirect
from django import forms

from google import get_nearby_places, byteify

from household.helpers import helper_get_me
from .helpers import helper_budget_categories, get_remaining_budget

from .forms import NewExpenseForm
from compare.models import MyBudgetCategory
from .models import MyExpenseItem

# from uscampgrounds.models import *
# camps = Campground.objects.all().distance(origin).order_by('distance')


# Capture a new expense item
@csrf_protect
@login_required
def new_expense(request):
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        location_message = None

        if request.method == 'POST':

            form = NewExpenseForm(request.POST)

            if form.is_valid():

                # Create expense record
                expense = MyExpenseItem()
                expense.note = form.cleaned_data.get('note')
                expense.amount = form.cleaned_data.get('amount')
                expense.household = me.get('household_obj')
                expense.who = me.get('account_obj')
                expense.category = MyBudgetCategory.objects.get(pk=form.cleaned_data.get('choose_category'))
                #expense.google_place = ''
                expense.save()
                messages.success(request, 'Your information has been saved.')

                remaining_budget = get_remaining_budget(form.cleaned_data.get('choose_category'))
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

        places = ''  # if using for choice, change to []
        place_types = []
        if position:
            nearby_json = byteify(get_nearby_places(position, 75))
            for place in nearby_json['results']:
                # item = (place['place_id'], place['name']) <-- use for choice in the future
                places += place['name'] + ' '
                place_types.append(place['types'])  # this is an array of arrays
            # places.sort(key=lambda items: items[1])

        if places:
            location_message = ('success','Geolocation information used for category selection assistance.')
        else:
            location_message = ('warning','Geolocation information not available. Unable to provide category selection assistance.')

        category_choices = helper_budget_categories(me.get('household_key'), place_types)
        form.fields['choose_category_place'].choices = category_choices[0]
        form.fields['choose_category'].choices = category_choices[1]

        context = {
            'form': form,
            'places': places,
            'page_title': 'Capture New Expense',
            'url': 'capture:new_expense',
            'location_message': location_message,
        }

        return render(request, 'capture/new_expense.html', context)


@login_required
def expenses(request):
    # Get household, validate active subscription
    me = helper_get_me(request.user.pk)
    if me.get('redirect'):
        return redirect('household:household_dashboard')
    else:

        context = {
         'page_title': 'Expenses',
         'url': 'capture:expenses',
        }

    return render(request, 'capture/expenses.html', context)
