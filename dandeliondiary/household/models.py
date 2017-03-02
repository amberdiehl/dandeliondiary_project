from __future__ import unicode_literals
from django.db import models

from django.utils import timezone


CHILDREN_STATUS_CHOICES = [(0, "No children"), (1, "Visit"), (2, "In household")]
GRANDCHILDREN_STATUS_CHOICES = [(0, "No grandchildren"), (1, "Visit"), (2, "In household")]
FUEL_CHOICES = [(1, "Diesel"), (2, "Electric"), (3, "Gasoline"), (4, "Hybrid"), (5, "Not Applicable")]
FINANCE_CHOICES = [(1, "Cash"), (2, "Gift"), (3, "Loan - Bank"), (4, "Loan - Dealer"), (5, "Loan - Private")]


# Household profile
class Household(models.Model):

    members_in_household = models.IntegerField()  # Adult members in household
    oldest_birthyear = models.IntegerField()  # Y/N senior in household
    budget_model = models.ForeignKey('core.BudgetModel')  # RV budget model
    opt_in_contribute = models.BooleanField(default=False, blank=True)  # Opt-in to utilize social aspects
    paid_through = models.DateField()  # Paid through
    subscription_status = models.CharField(max_length=7)  # 'Beta' 'Trial' 'Active' 'Expired'

    def __str__(self):
        return str(self.pk)


class RVHousehold(Household):
    # Type of RV'er
    start_year = models.IntegerField()  # Year first RV purchased
    rig_type = models.ForeignKey('core.RigType')  # trailer, 5th wheel, motorhome
    use_type = models.ForeignKey('core.UseType')  # primary residence, recreational
    income_type = models.ForeignKey('core.IncomeType')  # Workamp, Remote, Self employed, Investments
    pets_dog = models.IntegerField(default=0, blank=True)  # No. of dogs
    pets_cat = models.IntegerField(default=0, blank=True)  # No. of cats
    pets_other = models.IntegerField(default=0, blank=True)  # No. of other pets
    children = models.IntegerField(default=0, blank=True)  # No. of kids + household status
    children_status = models.IntegerField(default=0, blank=True, choices=CHILDREN_STATUS_CHOICES)
    grandchildren = models.IntegerField(default=0, blank=True)  # No. of grandchildren + household status
    grandchildren_status = models.IntegerField(default=0, blank=True, choices=GRANDCHILDREN_STATUS_CHOICES)
    created_date = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return str(self.pk)


# Household member profile
class Member(models.Model):
    account = models.OneToOneField('account.Account')
    phone_number = models.CharField(max_length=12)
    owner = models.BooleanField(default=False)
    newsletter = models.BooleanField(default=True)
    created_date = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return '%s' % self.phone_number


# Household members
class HouseholdMembers(models.Model):
    member_account = models.ForeignKey('account.Account')
    household_membership = models.ForeignKey(Household)

    def __str__(self):
        return 'Member key: %s  Household key: %s' % (self.member_account, self.household_membership)


# Household member pending invitations
class HouseholdInvite(models.Model):
    invite_household = models.ForeignKey(Household)
    email = models.EmailField(max_length=254)
    security_code = models.CharField(max_length=7, null=True, blank=True)
    invite_date = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return "".format(self.email)


# Household payments
class Payment(models.Model):
    household = models.ForeignKey(Household)
    payment_date = models.DateTimeField(default=timezone.now, blank=True)
    payment_amount = models.DecimalField(max_digits=5, decimal_places=2)
    payment_reference = models.CharField(max_length=128)
    payment_last4_digits = models.CharField(max_length=4)

    def __str__(self):
        return 'Hs key: %s  My key: %s' % (self.Household.pk, self.pk)


# Vehicles
class Vehicle(models.Model):
    household = models.ForeignKey(Household, blank=True, null=True)
    type = models.ForeignKey('core.VehicleType', blank=True)  # Trailer, 5th Wheel, Tow vehicle, TOAD Motorhome
    make = models.ForeignKey('core.VehicleMake', blank=True)
    model_name = models.ForeignKey('core.VehicleModel', blank=True)
    model_year = models.IntegerField(blank=True)
    fuel = models.IntegerField(blank=True, choices=FUEL_CHOICES)  # Diesel, Gas, Electric, Hybrid
    purchase_year = models.IntegerField(blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    purchase_type = models.ForeignKey('core.VehiclePurchaseType', blank=True)  # New, Used-Commercial, Used-Private
    finance = models.IntegerField(blank=True, choices=FINANCE_CHOICES)  # Cash, Gift, Loan, etc.
    satisfaction = models.ForeignKey('core.Satisfaction', blank=True)  # Love, Okay, Never again
    status = models.ForeignKey('core.VehicleStatus', blank=True)  # Mine, Sold, Salvage
    gone_year = models.IntegerField(default=0, blank=True)  # Sold/Salvage year

    def __str__(self):
        return '%s %s' % (self.make, self.model_name)
