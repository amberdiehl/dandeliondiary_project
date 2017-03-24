import re

from django.db.models import Count

from compare.models import MyBudgetGroup, MyBudgetCategory
from core.helpers import helpers_get_current_location_categories
from compare.helpers import helper_get_category_budget_and_expenses

from .models import MyExpenseItem

RE_VALID_EXPENSE_NOTE = re.compile(r'^[\w\d ,.\-=()*\+]{0,512}$')
RE_VALID_CATEGORY_NAME = re.compile(r'^[\w ]{1,50}$')
RE_VALID_DATE = re.compile(r'^\d{4}-\d{1,2}-\d{1,2}$')
RE_VALID_AMOUNT = re.compile(r'^[\d.]+$')
RE_VALID_HASH_KEY = re.compile(r'^[\w\d]{16}$')
RE_VALID_PAGE_VALUE = re.compile(r'^[\d]+$')


def helper_budget_categories(household, top_load=False, no_selection='------'):
    """
    Group is used to create tiered organization and cannot be selected. Child categories are collapsed with
    their parents, and it is the child key that is used so that expenses are associated with them.

    If requested (top_load=True), frequently used categories are placed first in the list. They are limited to
    top 5 and appear in the structure as if in a budget group, "Frequently Used".

    Category names are shortened if they contain "(e.g. ...)".

    The comma located at the end of each tuple add is what causes python to create tuples in tuples.
    """

    all_choices = (0, no_selection),

    if top_load:

        choices = ()

        top_categories = MyBudgetCategory.objects.filter(my_budget_group__household=household) \
            .values('my_category_name', 'id', 'parent_category', 'my_budget_group', )\
            .annotate(number_of_expenses=Count('myexpenseitem'))\
            .order_by('-number_of_expenses')\
            .filter(number_of_expenses__gt=0)[:5]

        for category in top_categories:

            choice = (category['id'],
                      composite_category_name(category['my_category_name'], category['parent_category'],
                                              category['my_budget_group']))
            choices += choice,

        if choices:
            group_choices = ('Frequently Used', choices)
            all_choices += group_choices,

    groups = MyBudgetGroup.objects.filter(household=household).order_by('group_list_order')
    for ndx, group in enumerate(groups):

        choices = ()

        categories = MyBudgetCategory.objects.filter(my_budget_group=group).filter(parent_category=None)\
            .order_by('my_category_name')

        for category in categories:

            children = MyBudgetCategory.objects.filter(parent_category=category).order_by('my_category_name')
            if children:

                for child in children:

                    choice = (child.pk, display_name(category.my_category_name) + ' - ' +
                              display_name(child.my_category_name))
                    choices += choice,
            else:

                choice = (category.pk, display_name(category.my_category_name))
                choices += choice,

        group_choices = ()
        if choices:
            group_choices = (group.my_group_name, choices)

        if group_choices:
            all_choices += group_choices,

    return all_choices


def helper_budget_categories_places(household, place_types):
    """
    Returns categories in pre-formatted HTML to be prepended to the category chooser.
    :param household: user's household
    :param place_types: google place types
    :return: HTML formatted for category chooser
    """

    categories_at_this_location = helpers_get_current_location_categories(place_types)

    all_choices = "<option value='0'>------</option>"
    all_choices += "<optgroup label='Geo Categories'>"

    categories = MyBudgetCategory.objects.filter(my_budget_group__household=household) \
        .filter(category_perma_key__in=categories_at_this_location) \
        .values_list('id', 'my_category_name', 'parent_category', 'my_budget_group') \
        .order_by('my_category_name')

    for category in categories:

        all_choices += "<option value='{}'>{}</option>"\
            .format(category[0],composite_category_name(category[1], category[2], category[3]))

    all_choices += '</optgroup>'

    return all_choices


def composite_category_name(name, my_parent, my_group):
    """
    Create a composite name for category when: 1) there's a parent (e.g. Parent Name - Child Name) or 2) in specific
    instances where category name alone is confusing by including group (e.g. Group Name - Category Name). This also
    calls the "display_name" function which truncates the category name to just the label, eliminating clarifying
    info, if it has it, e.g. (this, that, and another thing, etc.).

    Two examples of composites:

    "RV - Fuel" so as to distinguish from Fuel purchases associated with a tow vehicle. And "Pets - Insurance" to
    distinguish between insurance for vehicles, health care, etc.

    :param name: Name of the category
    :param my_parent: Either the key or object of the category's parent category
    :param my_group: Either the key or the object of the category's group
    :return: Category name formatted as specified above
    """
    if my_parent:
        if type(my_parent) is int:
            parent_category = MyBudgetCategory.objects.get(pk=my_parent)
        else:
            parent_category = my_parent
        category_name = parent_category.my_category_name + ' - ' + display_name(name)
    else:
        if name in ['Insurance', 'Other', ]:
            if type(my_group) is int:
                group = MyBudgetGroup.objects.get(pk=my_group)
            else:
                group = my_group
            category_name = group.my_group_name + ' - ' + display_name(name)
        else:
            category_name = display_name(name)

    return category_name


def display_name(name):
    """
    Remove "(e.g. ...)" from category names when displaying in dropdown selection box.
    """
    pos = name.find('(')
    if pos != -1:
        return name[0:pos]
    else:
        return name


def get_remaining_budget(c_id, date):
    """
    Get amount remaining in category budget.
    """

    # Get budget amount and related expenses based on expense effective date
    result = helper_get_category_budget_and_expenses(c_id, filter_date=date, fetch_expenses=True)

    return result['budget'] - result['expenses']


def is_expense_place_type(a, b):
    return not set(a).isdisjoint(b)


"""
  Validators for input associated with ajax views follow
"""


def validate_expense_inputs(date, amount, note):
    if re.match(RE_VALID_DATE, date) and re.match(RE_VALID_AMOUNT, amount) and re.match(RE_VALID_EXPENSE_NOTE, note):
        return True
    else:
        return False


def validate_expense_note_input(note):
    if re.match(RE_VALID_EXPENSE_NOTE, note):
        return True
    else:
        return False


def validate_filter_inputs(filter_values):

    error = False
    message = 'This filter has errors:<ul>'

    if filter_values['frDate'][0]:
        if not re.match(RE_VALID_DATE, filter_values['frDate'][0]):
            error = True
            message += '<li>Invalid from date.</li>'

    if filter_values['frDate'][0]:
        if not re.match(RE_VALID_DATE, filter_values['toDate'][0]):
            error = True
            message += '<li>Invalid to date.</li>'

    if filter_values['frAmount'][0]:
        if not re.match(RE_VALID_AMOUNT, filter_values['frAmount'][0]):
            error = True
            message += '<li>Invalid to from amount.</li>'

    if filter_values['toAmount'][0]:
        if not re.match(RE_VALID_AMOUNT, filter_values['toAmount'][0]):
            error = True
            message += '<li>Invalid from amount.</li>'

    if filter_values['inCategory'][0]:
        if not re.match(RE_VALID_CATEGORY_NAME, filter_values['inCategory'][0]):
            error = True
            message += '<li>Invalid characters provided for searching on category.</li>'

    if filter_values['inNote'][0]:
        if not re.match(RE_VALID_EXPENSE_NOTE, filter_values['inNote'][0]):
            error = True
            message += '<li>Invalid characters provided for searching on note.</li>'

    message += '</ul>'

    return error, message


def validate_id_input(hashed_id):
    if re.match(RE_VALID_HASH_KEY, hashed_id):
        return True
    else:
        return False


def validate_paging_input(page):
    if re.match(RE_VALID_PAGE_VALUE, page):
        return True
    else:
        return False
