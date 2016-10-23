from __future__ import unicode_literals

import datetime
from django.db import models


# My budget groups
class MyBudgetGroup(models.Model):
    household = models.ForeignKey("household.Household")
    my_group_name= models.CharField(max_length=20)
    group_description = models.TextField(default="description")
    group_perma_key = models.CharField(max_length=20, null=True, blank=True)
    group_list_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.my_group_name)


# My budget categories
class MyBudgetCategory(models.Model):
    my_budget_group = models.ForeignKey(MyBudgetGroup)
    my_category_name = models.CharField(max_length=50)
    parent_category = models.ForeignKey("self", null=True, blank=True)
    category_perma_key = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.my_category_name)


# Link google place types to categories
class MyCategorytoGoogleTypes(models.Model):
    category = models.ForeignKey(MyBudgetCategory)
    google_type = models.ForeignKey('core.GooglePlaceType')

    def __str__(self):
        return str(self.category)


# Budget for category
class MyBudget(models.Model):
    category = models.ForeignKey(MyBudgetCategory)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    annual_payment_month = models.IntegerField()
    note = models.TextField(default="")
    effective_date = models.DateField(default=datetime.datetime.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.pk)
