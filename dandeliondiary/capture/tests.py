import datetime
import json
import os

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from django.test import Client
from django.test import TestCase
from django.urls import reverse
from hashids import Hashids

from django.contrib.auth.models import User
from account.models import Account
from core.models import BudgetModel, RigType, UseType, IncomeType
from household.models import RVHousehold, HouseholdMembers, Member
from compare.models import MyBudgetGroup, MyBudgetCategory
from .models import *

import logging
log = logging.getLogger(__name__)

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16


# For now, all test cases for capture are defined in one class
class CaptureTest(TestCase):

    @classmethod
    def setUpClass(cls):

        try:
            budget_model = BudgetModel.objects.get(budget_model='RVHousehold')
        except ObjectDoesNotExist:
            budget_model = BudgetModel()
            budget_model.budget_model = 'RVHousehold'
            budget_model.budget_model_description = 'Budget model for RV community'
            budget_model.save()

        rig = RigType()
        rig.rig_type = 'test rig type'
        rig.rig_type_description = 'test rig type description'
        rig.save()

        use = UseType()
        use.use_type = 'test use type'
        use.use_type_description = 'test use type description'
        use.save()

        income = IncomeType()
        income.income_type = 'test income type'
        income.income_type_description = 'test income type description'
        income.save()

        user = User.objects.create_user('peggylee', email='peggylee@gmail.com', password='password')
        account = Account.objects.get(user=user)

        household = RVHousehold()
        household.members_in_household = 2
        household.oldest_birthyear = 1950
        household.budget_model = budget_model
        household.opt_in_contribute = True
        household.paid_through = datetime.datetime.now().date() + datetime.timedelta(days=1000)
        household.subscription_status = 'Beta'
        household.start_year = 2000
        household.rig_type = rig
        household.use_type = use
        household.income_type = income
        household.save()

        member = Member()
        member.account = account
        member.phone_number = '4152175899'
        member.owner = True
        member.newsletter = True
        member.save()

        household_member = HouseholdMembers()
        household_member.member_account = account
        household_member.household_membership = household
        household_member.save()

        group = MyBudgetGroup()
        group.household = household
        group.my_group_name = 'test group name'
        group.group_description = 'test group description'
        group.save()

        category = MyBudgetCategory()
        category.my_budget_group = group
        category.my_category_name = 'test category name'
        category.save()

        expenseitem = MyExpenseItem()
        expenseitem.note = 'MyExpenseItemTest'
        expenseitem.amount = 1.00
        expenseitem.household = household
        expenseitem.who = account
        expenseitem.category = category
        expenseitem.save()

        # remove media test image if test was run before
        filename = 'test.png'
        possible_previous_upload = settings.MEDIA_ROOT + '/' + MyReceipt._meta.get_field('receipt').upload_to + \
            '/' + filename
        try:
            os.remove(possible_previous_upload)
        except:
            pass

        path = settings.MEDIA_ROOT + '/' + filename
        uploaded_file = SimpleUploadedFile(name=filename, content=open(path, 'rb').read())

        receipt = MyReceipt()
        receipt.expense_item = expenseitem
        receipt.receipt = uploaded_file
        receipt.original_name = 'MyReceiptTest'
        receipt.save()

    @classmethod
    def tearDownClass(cls):

        # remove media test image
        filename = 'test.png'
        upload = settings.MEDIA_ROOT + '/' + MyReceipt._meta.get_field('receipt').upload_to + '/' + filename
        try:
            os.remove(upload)
        except:
            pass

    # Test expense item model
    def test_expense_model(self):
        expenseitem = MyExpenseItem.objects.get(note='MyExpenseItemTest')
        self.assertEquals(str(expenseitem), 'MyExpenseItemTest')

    # Test expense item receipt model
    def test_expense_receipt_model(self):
        receipt = MyReceipt.objects.get(original_name='MyReceiptTest')
        self.assertEquals(str(receipt), 'MyReceiptTest')

    # Test expense item delete receiver to ensure receipt has been deleted
    def test_expense_model_delete_receiver(self):

        file_deleted = False

        receipt = MyReceipt.objects.get(original_name='MyReceiptTest')
        receipt.delete()

        filename = 'test.png'
        path = settings.MEDIA_ROOT + '/' + MyReceipt._meta.get_field('receipt').upload_to + '/' + filename
        try:
            uploaded_file = SimpleUploadedFile(name=filename, content=open(path, 'rb').read())
        except IOError:
            file_deleted = True

        self.assertEquals(file_deleted, True)

    # Test the views to ensure a user must be logged or will be redirected to the login page
    def test_must_be_logged_in(self):

        # purposefully ensure client is NOT successfully logged in
        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='wrong')
        self.assertEquals(logged_in, False)

        # Test adding new expense view
        response = self.client.get(reverse('capture:new_expense'), follow=True, secure=True)
        chain = response.redirect_chain[0]
        self.assertEquals(chain[0], '/account/login/?next=/capture/new')
        self.assertEquals(chain[1], 302)
        self.assertEquals(response.status_code, 200)

        # Test exploring expense view
        response = self.client.get(reverse('capture:explore_expenses'), follow=True, secure=True)
        chain = response.redirect_chain[0]
        self.assertEquals(chain[0], '/account/login/?next=/capture/explore')
        self.assertEquals(chain[1], 302)
        self.assertEquals(response.status_code, 200)

        # Test supporting ajax view, listing expenses
        response = self.client.get('/capture/ajax/list_expenses/', follow=True, secure=True)
        chain = response.redirect_chain[0]
        self.assertEquals(chain[0], '/account/login/?next=/capture/ajax/list_expenses/')
        self.assertEquals(chain[1], 302)
        self.assertEquals(response.status_code, 200)

        # Test supporting ajax view that enables updates and deletes
        response = self.client.get('/capture/ajax/change_expense/d/', follow=True, secure=True)
        chain = response.redirect_chain[0]
        self.assertEquals(chain[0], '/account/login/?next=/capture/ajax/change_expense/d/')
        self.assertEquals(chain[1], 302)
        self.assertEquals(response.status_code, 200)

    # Test new expense view
    def test_new_expense(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        # Test successful get of view with user logged in
        response = self.client.get(reverse('capture:new_expense'), secure=True)
        self.assertEquals(response.status_code, 200)

        # Setup for posting new expense record
        user = User.objects.get(username='peggylee')
        account = Account.objects.get(user=user)
        household = RVHousehold.objects.get(householdmembers__member_account=account.pk)

        me = {
            'household_obj': household,
            'account_obj': account
        }

        category = MyBudgetCategory.objects.get(my_budget_group__household=household)

        form_data = {
            'note': 'what a note this is',
            'amount': 123,
            'choose_category': category.pk,
            'choose_category_place': 0,
            'me': me
        }

        response = self.client.post(reverse('capture:new_expense'), data=form_data, secure=True)
        self.assertEquals(response.status_code, 200)

    # Test explore expenses view
    def test_explore_expenses(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.post(reverse('capture:explore_expenses'), secure=True)
        self.assertEquals(response.status_code, 200)

    # Test ajax that gets expenses for explore expense view
    def test_ajax_list_expenses(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        user = User.objects.get(username='peggylee')
        account = Account.objects.get(user=user)
        household = RVHousehold.objects.get(householdmembers__member_account=account.pk)

        me = {
            'household_obj': household,
        }

        data = {
            'jtStartIndex': 0,
            'jtPageSize': 10,
            'me': me
        }

        response = self.client.get('/capture/ajax/list_expenses/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(result['Records'][0]['note'], 'MyExpenseItemTest')
        self.assertEquals(result['TotalRecordCount'], 1)

    # Test bad flag for changing/deleting an expense item
    def test_ajax_change_expense_flag(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        # Incorrect flag should result in 404
        response = self.client.get('/capture/ajax/change_expense/a/', secure=True)
        self.assertEquals(response.status_code, 404)

    # Test basic input validations for ajax enabling update of expense item
    def test_ajax_change_expense_update_fields_validation(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        # An invalid expense date, amount, or note is rejected
        data1 = {
            'id': '1234567890123456',  # passes basic validation but is not valid hash which is caught later
            'expense_date': '2017-01-3A',  # invalid
            'amount': 12.50,
            'note': 'i am a note'
        }
        data2 = {
            'id': '1234567890123456',
            'expense_date': '2017-01-31',
            'amount': 'AB',  # invalid
            'note': 'i am a note'
        }
        data3 = {
            'id': '1234567890123456',
            'expense_date': '2017-01-31',
            'amount': 12.50,
            'note': '$i am a note;'  # invalid
        }

        response = self.client.post('/capture/ajax/change_expense/u/', data=data1, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        response = self.client.post('/capture/ajax/change_expense/u/', data=data2, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        response = self.client.post('/capture/ajax/change_expense/u/', data=data3, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

    # Test validations for ID
    def test_ajax_change_expense_id_validation(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        # ID with invalid characters is rejected
        data = {
            'id': 'edk23fishjfhs;'
        }
        response = self.client.post('/capture/ajax/change_expense/d/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        # ID with valid hash be no record is rejected
        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        data = {
            'id': hashids.encode(99999999)
        }
        response = self.client.post('/capture/ajax/change_expense/d/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Message'], 'Error getting expense.')

    # TODO: Need to test household check by setting up another user, etc.

    # Test deleting an expense
    def test_ajax_change_expense_delete(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        user = User.objects.get(username='peggylee')
        account = Account.objects.get(user=user)
        expense_item = MyExpenseItem.objects.get(who=account)

        data = {
            'id': hashids.encode(expense_item.pk)
        }
        response = self.client.post('/capture/ajax/change_expense/d/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test updating an expense
    def test_ajax_change_expense_update(self):

        self.client = Client()
        logged_in = self.client.login(username='peggylee', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        user = User.objects.get(username='peggylee')
        account = Account.objects.get(user=user)
        expense_item = MyExpenseItem.objects.get(who=account)

        data = {
            'id': hashids.encode(expense_item.pk),
            'expense_date': '2017-01-01',
            'amount': 59.59,
            'note': 'I am a valid note.'
        }
        response = self.client.post('/capture/ajax/change_expense/u/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')
