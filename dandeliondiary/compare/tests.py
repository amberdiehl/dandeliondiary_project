import datetime
import json

from django.test import Client
from django.test import TestCase
from django.urls import reverse

from hashids import Hashids

from django.contrib.auth.models import User
from account.models import Account
from core.models import BudgetModel, RigType, UseType, IncomeType
from household.models import RVHousehold, Member, HouseholdMembers
from .models import MyBudgetGroup, MyBudgetCategory, MyBudget

HASH_SALT = 'nowis Ag00d tiM3for tW0BR3wskies'
HASH_MIN_LENGTH = 16


# For now, all test cases for compare are defined in one class
class CompareTest(TestCase):

    @classmethod
    def setUpClass(cls):

        # Build models associated with core app
        budget_model = BudgetModel()
        budget_model.budget_model = 'test budget model'
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

        """
        Create main test user and associated objects
        """
        user = User.objects.create_user('bobbysue', email='bobysue@no.com', password='password')
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
        group.my_group_name = 'Pets'
        group.group_description = 'Pet items'
        group.group_perma_key = 'perma-key-value'
        group.save()

        # Budget category without "child" categories--also cannot be deleted because of perma-key presence
        cat0 = MyBudgetCategory()
        cat0.my_budget_group = group
        cat0.my_category_name = 'Bedding'
        cat0.category_perma_key = 'perma-key-value'
        cat0.save()

        # Budget category with "child" categories--cannot have a budget associated with it
        cat1 = MyBudgetCategory()
        cat1.my_budget_group = group
        cat1.my_category_name = 'Eats'
        cat1.save()

        cat2 = MyBudgetCategory()
        cat2.my_budget_group = group
        cat2.my_category_name = 'Meals'
        cat2.parent_category = cat1
        cat2.save()

        cat3 = MyBudgetCategory()
        cat3.my_budget_group = group
        cat3.my_category_name = 'Snacks'
        cat3.parent_category = cat1
        cat3.save()

        # Two budget records for "Bedding"; this is the older one
        bud0 = MyBudget()
        bud0.category = cat0
        bud0.amount = 30.00
        bud0.annual_payment_month = 10
        bud0.note = 'Get me 1'
        bud0.effective_date = datetime.datetime.strptime('2016-01-01', '%Y-%m-%d')
        bud0.save()

        # Two budget records for "Bedding"; this is the newer one
        bud1 = MyBudget()
        bud1.category = cat0
        bud1.amount = 40.00
        bud1.annual_payment_month = 10
        bud1.note = 'Get me 2'
        bud1.effective_date = datetime.datetime.strptime('2017-01-01', '%Y-%m-%d')
        bud1.save()

        bud2 = MyBudget()
        bud2.category = cat2
        bud2.amount = 15.00
        bud2.annual_payment_month = 0
        bud2.effective_date = datetime.datetime.strptime('2016-01-01', '%Y-%m-%d')
        bud2.save()

        bud3 = MyBudget()
        bud3.category = cat3
        bud3.amount = 12.50
        bud3.annual_payment_month = 0
        bud3.effective_date = datetime.datetime.strptime('2016-02-01', '%Y-%m-%d')
        bud3.save()

        group = MyBudgetGroup()
        group.household = household
        group.my_group_name = 'Vehicles'
        group.group_description = 'Vehicle items'
        group.save()

        group = MyBudgetGroup()
        group.household = household
        group.my_group_name = 'Miscellaneous'
        group.group_description = 'Miscellaneous stuff'
        group.save()

        """
        Create user with expired subscription
        """
        user = User.objects.create_user('debbiesmith', email='debbiesmith@no.com', password='password')
        account = Account.objects.get(user=user)

        household = RVHousehold()
        household.members_in_household = 4
        household.oldest_birthyear = 1968
        household.budget_model = budget_model
        household.opt_in_contribute = True
        household.paid_through = datetime.datetime.strptime('2005-02-01', '%Y-%m-%d')
        household.subscription_status = 'Beta'
        household.start_year = 2000
        household.rig_type = rig
        household.use_type = use
        household.income_type = income
        household.save()

        member = Member()
        member.account = account
        member.phone_number = '6083225899'
        member.owner = True
        member.newsletter = True
        member.save()

        household_member = HouseholdMembers()
        household_member.member_account = account
        household_member.household_membership = household
        household_member.save()

        group = MyBudgetGroup()
        group.household = household
        group.my_group_name = 'Household'
        group.group_description = 'Household items'
        group.save()

    @classmethod
    def tearDownClass(cls):
        pass

    """
    Test the budget models.
    """
    def test_mybudgetgroup_model(self):
        group = MyBudgetGroup.objects.get(my_group_name='Pets')
        self.assertEquals(str(group), 'Pets')

    def test_mybudgetcategory_model(self):
        category = MyBudgetCategory.objects.get(my_category_name='Bedding')
        self.assertEquals(str(category), 'Bedding')

    def test_mybudget_model(self):
        budget = MyBudget.objects.get(pk=1)
        self.assertEquals(str(budget), '1')

    """
    Test redirect when household subscription has expired
    """
    def test_redirect_expired_subscription(self):

        self.client = Client()
        logged_in = self.client.login(username='debbiesmith', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('compare:compare_dashboard'), follow=True, secure=True)
        chain = response.redirect_chain[0]
        self.assertEquals(chain[0], '/household/settings')
        self.assertEquals(chain[1], 302)
        self.assertEquals(response.status_code, 200)

    """
    Test non-ajax views
    """
    def test_compare_dashboard(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('compare:compare_dashboard'), secure=True)
        self.assertEquals(response.status_code, 200)

    def test_compare_groups_categories(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('compare:groups_categories'), secure=True)
        self.assertEquals(response.status_code, 200)

    def test_compare_budget(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('compare:budget'), secure=True)
        self.assertEquals(response.status_code, 200)

    def test_compare_budgets_expenses(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('compare:budgets_expenses'), secure=True)
        self.assertEquals(response.status_code, 200)

    """
    Test all the ajax-based views
    """
    # Test ajax_dashboard_snapshot
    def test_ajax_dashboard_snapshot_bad_url_dt(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/dashboard_snapshot/aaaa-00-00/', secure=True)
        self.assertEquals(response.status_code, 404)

    def test_ajax_dashboard_snapshot_subscription_expired(self):

        self.client = Client()
        logged_in = self.client.login(username='debbiesmith', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/dashboard_snapshot/2017-01-31/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

    def test_ajax_dashboard_snapshot(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/dashboard_snapshot/2017-01-31/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'OK')

    # Test ajax_dashboard_month_series
    def test_ajax_dashboard_month_series(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/dashboard_month_series/2017-01-01/2017-12-01/',
                                   secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'OK')

    # Test ajax_dashboard_budget
    def testajax_dashboard_budget(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/dashboard_budget/2017-01-31/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'OK')

    # Test ajax_be_groups
    def test_ajax_be_groups(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/be_groups/2017-01-31/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_be_categories
    def test_ajax_be_categories(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        group = MyBudgetGroup.objects.get(my_group_name='Pets')
        pid = hashids.encode(group.pk)

        response = self.client.get('/compare/ajax/be_categories/' + pid + '/2017-01-31/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(len(result['Records']), 3)

    # Test ajax_list_groups
    def test_ajax_list_groups(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/list_groups/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(len(result['Records']), 3)

    # Test ajax_create_group
    def test_ajax_create_group(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        data0 = {
            'my_group_name': '$group',
            'group_description': 'new description',
            'group_list_order': 99
        }
        data1 = {
            'my_group_name': 'new group',
            'group_description': '$description',
            'group_list_order': 99
        }
        data2 = {
            'my_group_name': 'new group',
            'group_description': 'new description',
            'group_list_order': 'A'
        }

        response = self.client.post('/compare/ajax/create_group/', data=data0, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        response = self.client.post('/compare/ajax/create_group/', data=data1, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        response = self.client.post('/compare/ajax/create_group/', data=data2, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        user = User.objects.get(username='bobbysue')
        household = RVHousehold.objects.get(householdmembers__member_account=user.pk)
        data = {
            'household_obj': household,
            'my_group_name': 'Personal',
            'group_description': 'Personal items such as clothing, shoes, etc.',
            'group_list_order': 99
        }

        response = self.client.post('/compare/ajax/create_group/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(result['Record']['my_group_name'], 'Personal')

    # Test ajax_update_group
    def test_ajax_update_group(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        data0 = {
            'id': 'abcdefg'
        }

        response = self.client.post('/compare/ajax/update_group/', data=data0, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data1 = {
            'id': '1234567890123456',
            'my_group_name': 'new group',
            'group_description': '$description',
            'group_list_order': 99
        }

        response = self.client.post('/compare/ajax/update_group/', data=data1, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data2 = {
            'id': hashids.encode(99999999),
            'my_group_name': 'new group',
            'group_description': 'description',
            'group_list_order': 99
        }

        response = self.client.post('/compare/ajax/update_group/', data=data2, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')
        self.assertEquals(result['Message'], 'Error getting budget group.')

        group = MyBudgetGroup.objects.get(my_group_name='Household')  # Belongs to debbiesmith
        data3 = {
            'id': hashids.encode(group.pk),
            'my_group_name': 'group',
            'group_description': 'description',
            'group_list_order': 99,
        }
        response = self.client.post('/compare/ajax/update_group/', data=data3, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')
        self.assertEquals(result['Message'], 'Invalid request for budget group.')

        group = MyBudgetGroup.objects.get(my_group_name='Miscellaneous')
        data = {
            'id': hashids.encode(group.pk),
            'my_group_name': 'Miscellaneous',
            'group_description': 'Miscellaneous expenses',
            'group_list_order': 99,
        }
        response = self.client.post('/compare/ajax/update_group/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_delete_group
    def test_ajax_delete_group(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        # Invalid hash
        data0 = {
            'id': 'abcdefg'
        }
        response = self.client.post('/compare/ajax/delete_group/', data=data0, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        # Does not exist
        data1 = {
            'id': hashids.encode(99999999)
        }
        response = self.client.post('/compare/ajax/delete_group/', data=data1, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')
        self.assertEquals(result['Message'], 'Error getting budget group.')

        # Belongs to a different household
        group = MyBudgetGroup.objects.get(my_group_name='Household')  # Belongs to debbiesmith
        data2 = {
            'id': hashids.encode(group.pk)
        }
        response = self.client.post('/compare/ajax/delete_group/', data=data2, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')
        self.assertEquals(result['Message'], 'Invalid request for budget group.')

        # Is a core budget group item used for comparisons across households
        group = MyBudgetGroup.objects.get(my_group_name='Pets')
        data3 = {
            'id': hashids.encode(group.pk)
        }
        response = self.client.post('/compare/ajax/delete_group/', data=data3, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')
        self.assertEquals(result['Message'], 'Sorry, this is a core budget group used for comparisons and cannot be '
                                             'deleted.')

        # None of the above, it can be deleted
        group = MyBudgetGroup.objects.get(my_group_name='Miscellaneous')
        data = {
            'id': hashids.encode(group.pk)
        }
        response = self.client.post('/compare/ajax/delete_group/', data=data, secure=True)
        result = json.loads(response.content)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_list_categories
    def test_ajax_list_categories(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        # Flag 'p': return just parent categories; pid is group
        group = MyBudgetGroup.objects.get(my_group_name='Pets')
        response = self.client.get('/compare/ajax/list_categories/p/' + hashids.encode(group.pk) + '/', secure=True)
        result = json.loads(response.content)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(len(result['Records']), 2)

        # Flag 'h': parent with child categories mashed (2 become 1)
        group = MyBudgetGroup.objects.get(my_group_name='Pets')
        response = self.client.get('/compare/ajax/list_categories/h/' + hashids.encode(group.pk) + '/', secure=True)
        result = json.loads(response.content)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(len(result['Records']), 3)

        # Flag 'c': return just child categories; pid is parent category
        category = MyBudgetCategory.objects.get(my_category_name='Eats')
        response = self.client.get('/compare/ajax/list_categories/c/' + hashids.encode(category.pk) + '/', secure=True)
        result = json.loads(response.content)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(len(result['Records']), 2)

    # Test ajax_create_category
    def test_ajax_create_category(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        group = MyBudgetGroup.objects.get(my_group_name='Pets')
        pid = hashids.encode(group.pk)

        data0 = {
            'my_category_name': '$$bogus!;'
        }
        response = self.client.post('/compare/ajax/create_category/' + pid + '/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data = {
            'my_category_name': 'Vet'
        }
        response = self.client.post('/compare/ajax/create_category/' + pid + '/', data=data, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_update_category
    def test_ajax_update_category(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        data0 = {
            'id': 'dkkk52k3k',
        }
        response = self.client.post('/compare/ajax/update_category/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data1 = {
            'id': '1234567890123456',
            'my_category_name': '$$bogus!;'
        }
        response = self.client.post('/compare/ajax/update_category/', data=data1, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data2 = {
            'id': hashids.encode(99999999),
            'my_category_name': 'Bedding and stuff'
        }
        response = self.client.post('/compare/ajax/update_category/', data=data2, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        category = MyBudgetCategory.objects.get(my_category_name='Bedding')
        data = {
            'id': hashids.encode(category.pk),
            'my_category_name': 'Bedding and stuff'
        }
        response = self.client.post('/compare/ajax/update_category/', data=data, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_delete_category
    def test_ajax_delete_category(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        # Invalid hash
        data0 = {
            'id': 'dkkk52k3k',
        }
        response = self.client.post('/compare/ajax/delete_category/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        # Category not found
        data1 = {
            'id': hashids.encode(99999999),
        }
        response = self.client.post('/compare/ajax/delete_category/', data=data1, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        # Has perma-key
        category = MyBudgetCategory.objects.get(my_category_name='Bedding')
        data2 = {
            'id': hashids.encode(category.pk),
        }
        response = self.client.post('/compare/ajax/delete_category/', data=data2, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        category = MyBudgetCategory.objects.get(my_category_name='Eats')
        data = {
            'id': hashids.encode(category.pk),
        }
        response = self.client.post('/compare/ajax/delete_category/', data=data, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_create_child_category
    def test_ajax_create_child_category(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        parent_category = MyBudgetCategory.objects.get(my_category_name='Bedding')
        pid = hashids.encode(parent_category.pk)

        data0 = {
            'my_category_name': '$totally bogus$!;'
        }
        response = self.client.post('/compare/ajax/create_child_category/' + pid + '/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data = {
            'my_category_name': 'Outdoor lounging'
        }
        response = self.client.post('/compare/ajax/create_child_category/' + pid + '/', data=data, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_list_budgets
    def test_ajax_list_budgets(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        category = MyBudgetCategory.objects.get(my_category_name='Bedding')
        pid = hashids.encode(category.pk)

        response = self.client.get('/compare/ajax/list_budgets/' + pid + '/', secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')
        self.assertEquals(len(result['Records']), 2)

    # Test ajax_create_budget
    def test_ajax_create_budget(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)
        category = MyBudgetCategory.objects.get(my_category_name='Bedding')
        pid = hashids.encode(category.pk)

        data0 = {
            'amount': '123.aa',  # <--
            'annual_payment_month': 0,
            'note': 'This is a note.',
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/create_budget/' + pid + '/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data1 = {
            'amount': 123.00,
            'annual_payment_month': 'aa',  # <--
            'note': 'This is a note.',
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/create_budget/' + pid + '/', data=data1, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data2 = {
            'amount': 123.00,
            'annual_payment_month': 0,
            'note': '#$;This is a note!',  # <--
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/create_budget/' + pid + '/', data=data2, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data3 = {
            'amount': 123.00,
            'annual_payment_month': 0,
            'note': 'This is a note.',
            'effective_date': '2017-03-AA'  # <--
        }
        response = self.client.post('/compare/ajax/create_budget/' + pid + '/', data=data3, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data = {
            'amount': 75.00,
            'annual_payment_month': 10,
            'note': 'This is a note.',
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/create_budget/' + pid + '/', data=data, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_change_budget
    def test_ajax_change_budget(self):

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        hashids = Hashids(salt=HASH_SALT, min_length=HASH_MIN_LENGTH)

        data0 = {
            'id': 'ea9dks'
        }
        response = self.client.post('/compare/ajax/change_budget/d/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data1 = {
            'id': hashids.encode(1),
            'amount': '123.aa',  # <--
            'annual_payment_month': 0,
            'note': 'This is a note.',
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/change_budget/u/', data=data1, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data2 = {
            'id': hashids.encode(1),
            'amount': 123.00,
            'annual_payment_month': 'aa',  # <--
            'note': 'This is a note.',
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/change_budget/u/', data=data2, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data3 = {
            'id': hashids.encode(1),
            'amount': 123.00,
            'annual_payment_month': 0,
            'note': '#$;This is a note!',  # <--
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/change_budget/u/', data=data3, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data4 = {
            'id': hashids.encode(1),
            'amount': 123.00,
            'annual_payment_month': 0,
            'note': 'This is a note.',
            'effective_date': '2017-03-AA'  # <--
        }
        response = self.client.post('/compare/ajax/change_budget/u/', data=data4, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        data5 = {
            'id': hashids.encode(99999999)
        }
        response = self.client.post('/compare/ajax/change_budget/d/', data=data5, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        budget = MyBudget.objects.get(note='Get me 1')
        data_a = {
            'id': hashids.encode(budget.pk)
        }
        response = self.client.post('/compare/ajax/change_budget/d/', data=data_a, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

        budget = MyBudget.objects.get(note='Get me 2')
        data_b = {
            'id': hashids.encode(budget.pk),
            'amount': 75.00,
            'annual_payment_month': 10,
            'note': 'Need more money.',
            'effective_date': '2017-03-01'
        }
        response = self.client.post('/compare/ajax/change_budget/u/', data=data_b, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')

    # Test ajax_budget_summary
    def test_ajax_budget_summary(self):

        self.client = Client()
        logged_in = self.client.login(username='debbiesmith', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/budget_summary/', secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'ERROR')

        self.client = Client()
        logged_in = self.client.login(username='bobbysue', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get('/compare/ajax/budget_summary/', secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['Result'], 'OK')
