from __future__ import unicode_literals
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone


# Expense item
class MyExpenseItem(models.Model):
    note = models.CharField(max_length=512)
    amount = models.DecimalField(max_digits=11, decimal_places=2)
    household = models.ForeignKey('household.Household')
    who = models.ForeignKey('account.Account')
    category = models.ForeignKey('compare.MyBudgetCategory')
    google_place = models.ForeignKey('core.GooglePlaceDetail', null=True, blank=True)
    expense_date = models.DateField(default=timezone.now, blank=True)
    reconciled = models.BooleanField(default=False, blank=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True)

    def __str__(self):
        return self.note


# Receipt
class MyReceipt(models.Model):
    expense_item = models.ForeignKey(MyExpenseItem)
    receipt = models.ImageField(upload_to='receipts')
    original_name = models.CharField(max_length=256)

    def __str__(self):
        return self.original_name


# Note tags
class MyNoteTag(models.Model):
    household = models.ForeignKey('household.Household')
    tag = models.CharField(max_length=30)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("household", "tag")

    def __str__(self):
        return self.tag


# MyQuickAddCategoryAssociations enables preselection of category in the Quick Add feature based on Payee info.
class MyQuickAddCategoryAssociation(models.Model):
    household = models.ForeignKey('household.Household')
    payee_contains = models.CharField(max_length=80)
    category = models.ForeignKey('compare.MyBudgetCategory')

    class Meta:
        unique_together = ("household", "payee_contains")

    def __str__(self):
        return self.payee_contains


# Handler to delete receipt image file when receipt object is deleted
@receiver(post_delete, sender=MyReceipt)
def receipt_post_delete_handler(sender, **kwargs):
    receipt_obj = kwargs['instance']
    storage, path = receipt_obj.receipt.storage, receipt_obj.receipt.name
    if storage and path:
        storage.delete(path)
