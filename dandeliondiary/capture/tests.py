import os
import datetime
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from account.models import Account
from core.models import BudgetModel, RigType, UseType, IncomeType
from household.models import RVHousehold
from compare.models import MyBudgetGroup, MyBudgetCategory

from .models import *


# Test models
class CaptureModelsTest(TestCase):

    def setUp(self):

        user = User.objects.create_user('testuser', email='testuser@gmail.com', password='password')
        user.save()

        account = Account.objects.get(user=user)

        budget_model = BudgetModel()
        budget_model.budget_model = 'test buget model'
        budget_model.budget_model_description = 'test budget model description'
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

    def tearDown(self):
        # remove media test image
        filename = 'test.png'
        upload = settings.MEDIA_ROOT + '/' + MyReceipt._meta.get_field('receipt').upload_to + '/' + filename
        try:
            os.remove(upload)
        except:
            pass

    def test_expense_item_str(self):

        expenseitem = MyExpenseItem.objects.get(note='MyExpenseItemTest')
        self.assertEquals(str(expenseitem), 'MyExpenseItemTest')

    def test_expense_item_receipt(self):

        receipt = MyReceipt.objects.get(original_name='MyReceiptTest')
        self.assertEquals(str(receipt), 'MyReceiptTest')

    def test_delete_receiver(self):

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


class CaptureViewsTest(TestCase):

    def setUp(self):

        self.client = Client()
        self.user = User.objects.create_user('foobar', email='foobar@foobar.com', password='foobar')
        self.client.login(username='foobar', password='foobar')

    def test_login(self):
        self.assertTrue(self.user.is_authenticated())

    # All views require a logged in user to access them
    def test_must_be_logged_in(self):

        response = self.client.get('/capture/explore')
        self.assertEquals(response.status_code, 200)
