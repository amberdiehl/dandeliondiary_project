import datetime
import json

from django.core.exceptions import ObjectDoesNotExist

from django.test import Client
from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import User, Group
from account.models import Account
from core.models import BudgetModel, RigType, UseType, IncomeType, VehicleMake, VehicleModel, VehicleType, \
    VehiclePurchaseType, VehicleStatus, Satisfaction, BudgetGroup, BudgetCategory
from compare.models import MyBudgetGroup, MyBudgetCategory
from .models import RVHousehold, Member, HouseholdMembers, HouseholdInvite, Vehicle

from .forms import MyInfoForm, HouseholdProfileForm, InviteMemberForm, VehicleForm


# For now, all test cases for household are defined in one class
class HouseholdTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Set up initial test data
        :return:
        """

        """
        Create core model objects needed for household objects
        """
        try:
            budget_model = BudgetModel.objects.get(budget_model='RVHousehold')
        except ObjectDoesNotExist:
            budget_model = BudgetModel()
            budget_model.budget_model = 'RVHousehold'
            budget_model.budget_model_description = 'Budget model for RV community'
            budget_model.save()

        rig = RigType()
        rig.rig_type = 'Motorhome'
        rig.rig_type_description = 'Motorhome'
        rig.save()

        use = UseType()
        use.use_type = 'Full-time'
        use.use_type_description = 'Full-time'
        use.save()

        income = IncomeType()
        income.income_type = 'Self-employed'
        income.income_type_description = 'Self-employed'
        income.save()

        make = VehicleMake()
        make.filter = 'rv'
        make.make = 'Tiffin'
        make.save()

        model = VehicleModel()
        model.make = make
        model.model_name = 'Allegro Bus'
        model.save()

        v_type = VehicleType()
        v_type.filter = 'rv'
        v_type.type = 'Motorhome'
        v_type.type_description = 'Your RV is a motorhome.'
        v_type.save()

        purchase = VehiclePurchaseType()
        purchase.purchase_type = 'Used-Private'
        purchase.purchase_description = 'Purchased directly from an individual.'
        purchase.save()

        status = VehicleStatus()
        status.vehicle_status = 'Owner'
        status.vehicle_status_description = 'Still owned by me.'
        status.save()

        satisfaction = Satisfaction()
        satisfaction.satisfaction_index = 5
        satisfaction.satisfaction_description = 'Love it!'
        satisfaction.satisfaction_definition = 'Would definitely purchase again.'
        satisfaction.save()

        """
        Create auth group for forum permissions
        """
        group = Group()
        group.name = 'forum_customers'
        group.save()

        """
        Create template budget objects
        """
        budget_group = BudgetGroup()
        budget_group.budget_model = budget_model
        budget_group.group_name = 'Health Care'
        budget_group.group_description = 'Expenses associated with staying well'
        budget_group.group_list_order = 1
        budget_group.group_perma_key = 'perma-key-value'
        budget_group.save()

        category = BudgetCategory()
        category.budget_group = budget_group
        category.category = 'Insurance'
        category.category_perma_key = 'perma-key-value'
        category.save()

        """
        Create users and associated objects for dashboard test cases.
        """
        # 1. Just created account, has not setup household or provided personal details
        User.objects.create_user('alex', email='alex@no.com', password='password')

        # 2. New account, only has personal details
        user = User.objects.create_user('barney', email='barney@no.com', password='password')
        account = Account.objects.get(user=user)

        member = Member()
        member.account = account
        member.phone_number = '415-413-4393'
        member.owner = True
        member.newsletter = True
        member.save()

        user.first_name = 'Barney'
        user.last_name = 'Balderdash'
        user.save()

        # 3. New account, has provided personal details and household information, but no vehicles
        user = User.objects.create_user('chuck', email='chuck@no.com', password='password')
        account = Account.objects.get(user=user)

        member = Member()
        member.account = account
        member.phone_number = '415-413-4401'
        member.owner = True
        member.newsletter = True
        member.save()

        user.first_name = 'Charles'
        user.last_name = 'Carter'
        user.save()

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
        household.pets_dog = 1
        household.save()

        household_member = HouseholdMembers()
        household_member.member_account = account
        household_member.household_membership = household
        household_member.save()

        # 4. Expired account
        user = User.objects.create_user('dave', email='dave@no.com', password='password')
        account = Account.objects.get(user=user)

        member = Member()
        member.account = account
        member.phone_number = '415-413-4402'
        member.owner = True
        member.newsletter = True
        member.save()

        user.first_name = 'David'
        user.last_name = 'Davis'
        user.save()

        household = RVHousehold()
        household.members_in_household = 1
        household.oldest_birthyear = 1951
        household.budget_model = budget_model
        household.opt_in_contribute = True
        household.paid_through = datetime.datetime.now().date() - datetime.timedelta(days=1)
        household.subscription_status = 'Beta'
        household.start_year = 1985
        household.rig_type = rig
        household.use_type = use
        household.income_type = income
        household.pets_dog = 0
        household.save()

        household_member = HouseholdMembers()
        household_member.member_account = account
        household_member.household_membership = household
        household_member.save()

        """
        Create users and associated objects for my info test cases.
        """
        User.objects.create_user('eric', email='eric@no.com', password='password')

        """
        Create users and associated objects for household test cases.
        """
        User.objects.create_user('fred', email='fred@no.com', password='password')

        """
        Create users and associated objects for household member test cases.
        """
        # Expired membership
        user = User.objects.create_user('greg', email='greg@no.com', password='password')
        account = Account.objects.get(user=user)

        member = Member()
        member.account = account
        member.phone_number = '415-413-4410'
        member.owner = True
        member.newsletter = True
        member.save()

        user.first_name = 'Greg'
        user.last_name = 'Gardiner'
        user.save()

        household = RVHousehold()
        household.members_in_household = 2
        household.oldest_birthyear = 1954
        household.budget_model = budget_model
        household.opt_in_contribute = True
        household.paid_through = datetime.datetime.now().date() - datetime.timedelta(days=1)
        household.subscription_status = 'Beta'
        household.start_year = 1982
        household.rig_type = rig
        household.use_type = use
        household.income_type = income
        household.pets_dog = 1
        household.save()

        household_member = HouseholdMembers()
        household_member.member_account = account
        household_member.household_membership = household
        household_member.save()

        # Current membership
        user = User.objects.create_user('harry', email='harry@no.com', password='password')
        account = Account.objects.get(user=user)

        member = Member()
        member.account = account
        member.phone_number = '415-413-4411'
        member.owner = True
        member.newsletter = True
        member.save()

        user.first_name = 'Harry'
        user.last_name = 'Hughes'
        user.save()

        household = RVHousehold()
        household.members_in_household = 2
        household.oldest_birthyear = 1951
        household.budget_model = budget_model
        household.opt_in_contribute = True
        household.paid_through = datetime.datetime.now().date() + datetime.timedelta(days=1000)
        household.subscription_status = 'Beta'
        household.start_year = 1980
        household.rig_type = rig
        household.use_type = use
        household.income_type = income
        household.pets_dog = 2
        household.save()

        household_member = HouseholdMembers()
        household_member.member_account = account
        household_member.household_membership = household
        household_member.save()

        # Member of harry's household
        user = User.objects.create_user('annie', email='annie@no.com', password='password')
        account = Account.objects.get(user=user)

        member = Member()
        member.account = account
        member.phone_number = '415-413-5511'
        member.owner = False
        member.newsletter = True
        member.save()

        user.first_name = 'Annie'
        user.last_name = 'Arneau-Hughes'
        user.save()

        household_member = HouseholdMembers()
        household_member.member_account = account
        household_member.household_membership = household
        household_member.save()

        # Random invites for tests
        invite = HouseholdInvite()
        invite.invite_household = household
        invite.email = 'abc123@no.com'
        invite.security_code = '1234567'
        invite.invite_date = datetime.datetime.now().date()
        invite.save()

        invite = HouseholdInvite()
        invite.invite_household = household
        invite.email = 'abc456@no.com'
        invite.security_code = '1234567'
        invite.invite_date = datetime.datetime.now().date()
        invite.save()

    @classmethod
    def tearDownClass(cls):
        pass

    """
    Test the models
    """
    def test_models(self):

        budget_model = BudgetModel.objects.get(budget_model='RVHousehold')
        self.assertEquals(str(budget_model), 'RVHousehold')

        rig = RigType.objects.get(rig_type='Motorhome')
        self.assertEquals(str(rig), 'Motorhome')

        use = UseType.objects.get(use_type='Full-time')
        self.assertEquals(str(use), 'Full-time')

        income = IncomeType.objects.get(income_type='Self-employed')
        self.assertEquals(str(income), 'Self-employed')

        make = VehicleMake.objects.get(make='Tiffin')
        self.assertEquals(str(make), 'Tiffin')

        v_model = VehicleModel.objects.get(model_name='Allegro Bus')
        self.assertEquals(str(v_model), 'Allegro Bus')

        v_type = VehicleType.objects.get(type='Motorhome')
        self.assertEquals(str(v_type), 'Motorhome')

        purchase = VehiclePurchaseType.objects.get(purchase_type='Used-Private')
        self.assertEquals(str(purchase), 'Used-Private')

        status = VehicleStatus.objects.get(vehicle_status='Owner')
        self.assertEquals(str(status), 'Owner')

        satisfaction = Satisfaction.objects.get(satisfaction_index=5)
        self.assertEquals(str(satisfaction), 'Love it!')

        member = Member.objects.get(phone_number='415-413-4393')
        self.assertEquals(str(member), '415-413-4393')

        household = RVHousehold.objects.get(pk=1)
        self.assertEquals(str(household), '1')

        household_member = HouseholdMembers.objects.all()[0]
        self.assertEquals(str(household_member), 'Member key: {}  Household key: {}'.format(
            household_member.member_account,
            household_member.household_membership))

        budget_group = BudgetGroup.objects.get(group_name='Health Care')
        self.assertEquals(str(budget_group), 'Health Care')

        category = BudgetCategory.objects.get(category='Insurance')
        self.assertEquals(str(category), 'Insurance')

        invite = HouseholdInvite.objects.get(email='abc123@no.com')
        self.assertEquals(str(invite), 'abc123@no.com')

    """
    Test various states and conditions for the dashboard view
    """
    def test_dashboard_new_user(self):
        """
        New user, hasn't setup personal information or household yet
        :return:
        """
        self.client = Client()
        logged_in = self.client.login(username='alex', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('household:household_dashboard'), secure=True)
        summary = response.context['summary']

        # Tags indicating need for personal info and household information should exist
        self.assertEquals(summary['need_myinfo'], 'Please take a moment to provide your name and a phone number.')
        self.assertEquals(summary['need_household'],
                          'To activate your free trial, please setup your household information.')

        # And other tags should not exist until after those things are provided
        with self.assertRaises(KeyError):
            test = summary['need_vehicles']
            test = summary['free_trial']

    def test_dashboard_new_user_personal_info_provided(self):
        """
        New user, has setup personal information but not household yet
        :return:
        """
        self.client = Client()
        logged_in = self.client.login(username='barney', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('household:household_dashboard'), secure=True)
        summary = response.context['summary']

        # Personal info for Barney should exist
        self.assertEquals(summary['first_name'], 'Barney')
        self.assertEquals(summary['last_name'], 'Balderdash')
        self.assertEquals(summary['phone_number'], '415-413-4393')

        # Household info is still missing
        self.assertEquals(summary['need_household'],
                          'To activate your free trial, please setup your household information.')

        # And other tags should not exist until after those things are provided
        with self.assertRaises(KeyError):
            test = summary['need_vehicles']
            test = summary['free_trial']

    def test_dashboard_new_user_with_household_setup(self):
        """
        New user, has provided personal info and household
        :return:
        """
        self.client = Client()
        logged_in = self.client.login(username='chuck', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('household:household_dashboard'), secure=True)
        summary = response.context['summary']

        # Personal info for Charles should exist
        self.assertEquals(summary['first_name'], 'Charles')
        self.assertEquals(summary['last_name'], 'Carter')
        self.assertEquals(summary['phone_number'], '415-413-4401')

        # Household info should exist
        self.assertEquals(summary['start_year'], 2000)
        self.assertEquals(summary['pets'], 1)

        # And now info is displayed about subscription and vehicles
        self.assertEquals(summary['need_vehicles'][0:14], 'Please specify')
        self.assertEquals(summary['free_trial'][0:6], 'Thanks')

    def test_dashboard_expired_subscription(self):
        """
        Expired subscription
        :return:
        """
        self.client = Client()
        logged_in = self.client.login(username='dave', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('household:household_dashboard'), secure=True)
        summary = response.context['summary']

        # Personal info for David should exist
        self.assertEquals(summary['first_name'], 'David')
        self.assertEquals(summary['last_name'], 'Davis')
        self.assertEquals(summary['phone_number'], '415-413-4402')

        # Household info should exist
        self.assertEquals(summary['start_year'], 1985)
        self.assertEquals(summary['pets'], 0)

        # And now info is displayed about subscription and vehicles
        self.assertEquals(summary['need_vehicles'][0:14], 'Please specify')
        self.assertEquals(summary['expired'][0:30], 'Your subscription has expired.')

    """
    Test my_info view and form
    """
    def test_my_info_view(self):

        self.client = Client()
        logged_in = self.client.login(username='eric', password='password')
        self.assertEquals(logged_in, True)

        data = {
            'first_name': 'Eric',
            'last_name': 'Emmerson',
            'phone_number': '415-413-4403',
            'newsletter': True,
            'owner': True
        }

        response = self.client.post(reverse('household:my_info'), data=data, secure=True)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username='eric')
        account = Account.objects.get(user=user)
        member = Member.objects.get(account=account)

        self.assertEquals(user.last_name, 'Emmerson')
        self.assertEquals(member.phone_number, '415-413-4403')

    def test_my_info_form_empty(self):

        data = {
            'first_name': '',
            'last_name': '',
            'phone_number': '',
            'newsletter': True,
            'owner': True
        }
        form = MyInfoForm(data=data)
        self.assertFalse(form.is_valid())

    def test_my_info_form_bad_names(self):

        data = {
            'first_name': '$',
            'last_name': 'E',
            'phone_number': '415-413-4403',
            'newsletter': True,
            'owner': True
        }
        form = MyInfoForm(data=data)
        self.assertFalse(form.is_valid())

    def test_my_info_form_bad_phone_number(self):

        data = {
            'first_name': 'Eric',
            'last_name': 'Emmerson',
            'phone_number': '555-555-5555',
            'newsletter': True,
            'owner': True
        }
        form = MyInfoForm(data=data)
        self.assertFalse(form.is_valid())

    def test_my_info_form_valid(self):

        data = {
            'first_name': 'Eric',
            'last_name': 'Emmerson',
            'phone_number': '415-413-4403',
            'newsletter': True,
            'owner': True
        }
        form = MyInfoForm(data=data)
        self.assertTrue(form.is_valid())

    """
    Test household_profile view and form
    """
    def test_household_profile_view(self):

        self.client = Client()
        logged_in = self.client.login(username='fred', password='password')
        self.assertEquals(logged_in, True)

        rig= RigType.objects.get(rig_type='Motorhome')
        use = UseType.objects.get(use_type='Full-time')
        income = IncomeType.objects.get(income_type='Self-employed')

        # Test create
        data = {
            'start_year': 1992,
            'members_in_household': 2,
            'oldest_birthyear': 1952,
            'rig_type': rig.pk,
            'use_type': use.pk,
            'income_type': income.pk,
            'pets_dog': 1,
            'pets_cat': 0,
            'pets_other': 1,
            'children': 0,
            'children_status': 0,
            'grandchildren': 0,
            'grandchildren_status': 0
        }

        response = self.client.post(reverse('household:maintain_household'), data=data, secure=True)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username='fred')
        account = Account.objects.get(user=user)

        household = RVHousehold.objects.get(householdmembers__member_account=account)
        self.assertEquals(household.start_year, 1992)

        my_group = MyBudgetGroup.objects.get(my_group_name='Health Care')
        self.assertEquals(str(my_group), 'Health Care')

        my_category = MyBudgetCategory.objects.get(my_category_name='Insurance')
        self.assertEquals(str(my_category), 'Insurance')

        # Test update
        data = {
            'start_year': 1994,
            'members_in_household': 2,
            'oldest_birthyear': 1952,
            'rig_type': rig.pk,
            'use_type': use.pk,
            'income_type': income.pk,
            'pets_dog': 1,
            'pets_cat': 1,
            'pets_other': 0,
            'children': 0,
            'children_status': 0,
            'grandchildren': 0,
            'grandchildren_status': 0
        }

        response = self.client.post(reverse('household:maintain_household'), data=data, secure=True)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username='fred')
        account = Account.objects.get(user=user)

        household = RVHousehold.objects.get(householdmembers__member_account=account)
        self.assertEquals(household.start_year, 1994)

    def test_household_profile_form_empty(self):

        data = {
            'start_year': 0,
            'members_in_household': 0,
            'oldest_birthyear': 0,
            'rig_type': 0,
            'use_type': 0,
            'income_type': 0,
            'pets_dog': 0,
            'pets_cat': 0,
            'pets_other': 0,
            'children': 0,
            'children_status': 0,
            'grandchildren': 0,
            'grandchildren_status': 0
        }
        form = HouseholdProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_household_profile_form_need_rig_use_income(self):
        data = {
            'start_year': 2011,
            'members_in_household': 2,
            'oldest_birthyear': 1963,
            'rig_type': 0,
            'use_type': 0,
            'income_type': 0,
            'pets_dog': 0,
            'pets_cat': 0,
            'pets_other': 0,
            'children': 0,
            'children_status': 0,
            'grandchildren': 0,
            'grandchildren_status': 0
        }
        form = HouseholdProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_household_profile_form_too_many_pets(self):
        data = {
            'start_year': 2011,
            'members_in_household': 2,
            'oldest_birthyear': 1963,
            'rig_type': 1,
            'use_type': 1,
            'income_type': 1,
            'pets_dog': 11,
            'pets_cat': 0,
            'pets_other': 0,
            'children': 0,
            'children_status': 0,
            'grandchildren': 0,
            'grandchildren_status': 0
        }
        form = HouseholdProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_household_profile_form_invalid_children_status(self):
        data = {
            'start_year': 2011,
            'members_in_household': 2,
            'oldest_birthyear': 1963,
            'rig_type': 1,
            'use_type': 1,
            'income_type': 1,
            'pets_dog': 1,
            'pets_cat': 0,
            'pets_other': 0,
            'children': 1,
            'children_status': 0,  # <--
            'grandchildren': 1,
            'grandchildren_status': 0  # <--
        }
        form = HouseholdProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_household_profile_form_invalid_children_count(self):
        data = {
            'start_year': 2011,
            'members_in_household': 2,
            'oldest_birthyear': 1963,
            'rig_type': 1,
            'use_type': 1,
            'income_type': 1,
            'pets_dog': 1,
            'pets_cat': 0,
            'pets_other': 0,
            'children': 0,  # <--
            'children_status': 1,
            'grandchildren': 0,  # <--
            'grandchildren_status': 1
        }
        form = HouseholdProfileForm(data=data)
        self.assertFalse(form.is_valid())

    def test_household_profile_form_valid(self):
        data = {
            'start_year': 2011,
            'members_in_household': 2,
            'oldest_birthyear': 1963,
            'rig_type': 1,
            'use_type': 1,
            'income_type': 1,
            'pets_dog': 1,
            'pets_cat': 1,
            'pets_other': 0,
            'children': 0,
            'children_status': 0,
            'grandchildren': 0,
            'grandchildren_status': 0
        }
        form = HouseholdProfileForm(data=data)
        self.assertTrue(form.is_valid())

    """
    Test household_members view, form, and ajax calls
    """
    def test_household_members_view(self):

        self.client = Client()

        # Redirect for expired subscription
        logged_in = self.client.login(username='greg', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('household:maintain_members'), follow=True, secure=True)
        chain = response.redirect_chain[0]
        self.assertEquals(chain[0], '/household/settings')
        self.assertEquals(chain[1], 302)
        self.assertEquals(response.status_code, 200)

        # Redirect because non-owner cannot invite other members
        logged_in = self.client.login(username='annie', password='password')
        self.assertEquals(logged_in, True)

        response = self.client.get(reverse('household:maintain_members'), follow=True, secure=True)
        chain = response.redirect_chain[0]
        self.assertEquals(chain[0], '/household/settings')
        self.assertEquals(chain[1], 302)
        self.assertEquals(response.status_code, 200)

        # Test invitation
        logged_in = self.client.login(username='harry', password='password')
        self.assertEquals(logged_in, True)

        data = {
            'email': 'harry+invite1@no.com'
        }
        response = self.client.post(reverse('household:maintain_members'), data=data, secure=True)
        self.assertEqual(response.status_code, 200)

        current = response.context['current'].filter(username='annie')
        self.assertEquals(len(current), 1)

        pending = response.context['pending'].filter(email='abc123@no.com')
        self.assertEquals(len(pending), 1)

        invite = HouseholdInvite.objects.get(email='harry+invite1@no.com')
        self.assertEquals(str(invite), 'harry+invite1@no.com')

    def test_member_invite_form_email_already_exists_account(self):

        data = {
            'email': 'barney@no.com'
        }
        form = InviteMemberForm(data=data)
        self.assertFalse(form.is_valid())

    def test_member_invite_form_email_already_exists_invite(self):

        data = {
            'email': 'abc456@no.com'
        }
        form = InviteMemberForm(data=data)
        self.assertFalse(form.is_valid())

    def test_member_invite_form_email_invalid(self):

        data = {
            'email': 'nono.nono.com'
        }
        form = InviteMemberForm(data=data)
        self.assertFalse(form.is_valid())

    def test_member_invite_form_email_valid(self):

        data = {
            'email': 'bettylou@no.com'
        }
        form = InviteMemberForm(data=data)
        self.assertTrue(form.is_valid())

    def test_ajax_delete_invite(self):

        self.client = Client()
        logged_in = self.client.login(username='harry', password='password')
        self.assertEquals(logged_in, True)

        # Invalid data tests
        data0 = {
            'id': '$',  # <--
            'user': 'harry'
        }
        response = self.client.post('/household/ajax/delete-invite/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        data1 = {
            'id': 99999999,
            'user': '$rie9%!'  # <--
        }
        response = self.client.post('/household/ajax/delete-invite/', data=data1, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        # Invalid id; does not exist
        data2 = {
            'id': 99999999,
            'user': 'harry'
        }
        response = self.client.post('/household/ajax/delete-invite/', data=data2, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        # Validate user name provided is same as user name logged in
        data3 = {
            'id': 99999999,
            'user': 'greg'
        }
        response = self.client.post('/household/ajax/delete-invite/', data=data3, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        invite = HouseholdInvite.objects.get(email='abc123@no.com')
        data = {
            'id': invite.pk,
            'user': 'harry'
        }
        response = self.client.post('/household/ajax/delete-invite/', data=data, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'OK')

        invite = HouseholdInvite.objects.filter(email='abc123@no.com')
        self.assertEquals(len(invite), 0)

    def test_ajax_change_member_status(self):

        self.client = Client()
        logged_in = self.client.login(username='harry', password='password')
        self.assertEquals(logged_in, True)

        # Invalid data tests
        data0 = {
            'username': 'annie',
            'user': '$',  # <--
            'status': 'Deactivate'
        }
        response = self.client.post('/household/ajax/change-member-status/', data=data0, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        data1 = {
            'username': 'annie',
            'user': 'harry',
            'status': 'Off'  # <--
        }
        response = self.client.post('/household/ajax/change-member-status/', data=data1, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        # User (username) does not exist
        data2 = {
            'username': 'ann-marie',
            'user': 'harry',
            'status': 'Deactivate'
        }
        response = self.client.post('/household/ajax/change-member-status/', data=data2, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        # User (username) is not member of given household (user)
        data3 = {
            'username': 'annie',
            'user': 'greg',
            'status': 'Deactivate'
        }
        response = self.client.post('/household/ajax/change-member-status/', data=data3, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'ERROR')

        # Deactivate user (username) account
        data_a = {
            'username': 'annie',
            'user': 'harry',
            'status': 'Deactivate'
        }
        response = self.client.post('/household/ajax/change-member-status/', data=data_a, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'OK')

        user = User.objects.get(username='annie')
        self.assertFalse(user.is_active)

        # Reactivate user (username) account
        data_b = {
            'username': 'annie',
            'user': 'harry',
            'status': 'Activate'
        }
        response = self.client.post('/household/ajax/change-member-status/', data=data_b, secure=True)
        result = json.loads(response.content)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(result['status'], 'OK')

        user = User.objects.get(username='annie')
        self.assertTrue(user.is_active)

    """
    Test household_vehicles view, form, and ajax calls
    """
    def test_household_vehicles_view(self):

        self.client = Client()
        logged_in = self.client.login(username='harry', password='password')
        self.assertEquals(logged_in, True)

        # Setup by getting objects for foreign keys
        vehicle_type = VehicleType.objects.get(type='Motorhome')
        vehicle_make = VehicleMake.objects.get(make='Tiffin')
        vehicle_model = VehicleModel.objects.get(model_name='Allegro Bus')
        purchase_type = VehiclePurchaseType.objects.get(purchase_type='Used-Private')
        satisfaction = Satisfaction.objects.get(satisfaction_index=5)
        vehicle_status = VehicleStatus.objects.get(vehicle_status='Owner')

        # Data to create vehicle record
        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-type': vehicle_type,
            'form-0-make': vehicle_make,
            'form-0-model_name': vehicle_model,
            'form-0-model_year': 2006,
            'form-0-fuel': 'Diesel',
            'form-0-purchase_year': 2015,
            'form-0-purchase_price': 50000.00,
            'form-0-purchase_type': purchase_type,
            'form-0-finance': 'Cash',
            'form-0-satisfaction': satisfaction,
            'form-0-status': vehicle_status,
            'form-0-gone_year': 0
        }

        response = self.client.post(reverse('household:maintain_vehicles'), data=data, secure=True)
        self.assertEqual(response.status_code, 200)

    def test_vehicle_form_empty(self):

        data = {
            'type': 0,
            'make': 0,
            'model_name': 0,
            'model_year': 0,
            'fuel': 0,
            'purchase_year': 0,
            'purchase_price': 0,
            'purchase_type': 0,
            'finance': 0,
            'satisfaction': 0,
            'status': 0,
            'gone_year': 0
        }
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())

    def test_vehicle_form_bad_model_year(self):

        data = {
            'type': 1,
            'make': 1,
            'model_name': 1,
            'model_year': 1800,
            'fuel': 1,
            'purchase_year': 2016,
            'purchase_price': 50.00,
            'purchase_type': 1,
            'finance': 1,
            'satisfaction': 1,
            'status': 1,
            'gone_year': 0
        }
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())

        data['model_year'] = 2080
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())

    def test_vehicle_form_bad_purchase_year(self):

        data = {
            'type': 1,
            'make': 1,
            'model_name': 1,
            'model_year': 2016,
            'fuel': 1,
            'purchase_year': 1900,  # <-- too far in the past
            'purchase_price': 50.00,
            'purchase_type': 1,
            'finance': 1,
            'satisfaction': 1,
            'status': 1,
            'gone_year': 0
        }
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())

        data['purchase_year'] = 2080  # <-- too far into the future
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())

    def test_vehicle_form_bad_purchase_price(self):

        data = {
            'type': 1,
            'make': 1,
            'model_name': 1,
            'model_year': 2016,
            'fuel': 1,
            'purchase_year': 2016,
            'purchase_price': .99,
            'purchase_type': 1,
            'finance': 1,
            'satisfaction': 1,
            'status': 1,
            'gone_year': 0
        }
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())

    def test_vehicle_form_gone_year_in_future(self):

        data = {
            'type': 1,
            'make': 1,
            'model_name': 1,
            'model_year': 2012,
            'fuel': 1,
            'purchase_year': 2014,
            'purchase_price': 50000.00,
            'purchase_type': 1,
            'finance': 1,
            'satisfaction': 1,
            'status': 1,
            'gone_year': 2080
        }
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())

    def test_vehicle_form_valid(self):

        data = {
            'type': 1,
            'make': 1,
            'model_name': 1,
            'model_year': 2012,
            'fuel': 1,
            'purchase_year': 2014,
            'purchase_price': 50000.00,
            'purchase_type': 1,
            'finance': 1,
            'satisfaction': 1,
            'status': 1,
            'gone_year': 0
        }
        form = VehicleForm(data=data)
        self.assertTrue(form.is_valid())

    def test_ajax_makes_by_type(self):

        vehicle_type = VehicleType.objects.get(type='Motorhome')

        response = self.client.get('/household/ajax/makes-by-type/' + str(vehicle_type.pk) + '/', secure=True)
        result = json.loads(response.content)

        make = VehicleMake.objects.filter(filter=vehicle_type.filter)[0]
        self.assertTrue(str(make.pk) in result)

    def test_ajax_models_by_make(self):

        vehicle_make = VehicleMake.objects.get(make='Tiffin')

        response = self.client.get('/household/ajax/models-by-make/' + str(vehicle_make.pk) + '/', secure=True)
        result = json.loads(response.content)

        model = VehicleModel.objects.filter(make=vehicle_make)[0]
        self.assertTrue(str(model.pk) in result)

    def test_ajax_add_make(self):

        self.client = Client()
        logged_in = self.client.login(username='harry', password='password')
        self.assertEquals(logged_in, True)

        vehicle_type = VehicleType.objects.get(type='Motorhome')
        response = self.client.post('/household/ajax/add-make/' + str(vehicle_type.pk) + '/JayCo/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(result['status'], 'OK')

        make = VehicleMake.objects.get(pk=result['key'])
        self.assertEquals(make.make, 'Jayco')

    def test_ajax_add_model(self):

        self.client = Client()
        logged_in = self.client.login(username='harry', password='password')
        self.assertEquals(logged_in, True)

        make = VehicleMake.objects.get(make='Tiffin')
        response = self.client.post('/household/ajax/add-model/' + str(make.pk) + '/Phaeton/', secure=True)
        result = json.loads(response.content)

        self.assertEquals(result['status'], 'OK')

        vehicle_model = VehicleModel.objects.get(pk=result['key'])
        self.assertEquals(vehicle_model.model_name, 'Phaeton')
