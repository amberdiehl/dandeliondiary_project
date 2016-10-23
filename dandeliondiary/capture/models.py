from __future__ import unicode_literals
import datetime
from django.db import models


# Expense item
class MyExpenseItem(models.Model):
    note = models.CharField(max_length=512)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    household = models.ForeignKey('household.Household')
    who = models.ForeignKey('account.Account')
    category = models.ForeignKey('compare.MyBudgetCategory')
    google_place = models.ForeignKey('core.GooglePlaceDetail', null=True, blank=True)
    expense_date = models.DateField(default=datetime.datetime.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.note
