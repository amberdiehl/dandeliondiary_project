from __future__ import unicode_literals
from django.db import models

from django.utils import timezone


# Income type
class IncomeType(models.Model):
    income_type = models.CharField(max_length=32)
    income_type_description = models.TextField(default="description")

    def __str__(self):
        return str(self.income_type)


# Use type
class UseType(models.Model):
    use_type = models.CharField(max_length=32)
    use_type_description = models.TextField(default="description")

    def __str__(self):
        return str(self.use_type)


# Vehicle make
class VehicleMake(models.Model):
    filter = models.CharField(max_length=12, null=True, blank=True)
    make = models.CharField(max_length=50)

    def __str__(self):
        return str(self.make)


# Vehicle model
class VehicleModel(models.Model):
    make = models.ForeignKey(VehicleMake)
    model_name = models.CharField(max_length=128)

    def __str__(self):
        return str(self.model_name)


# Vehicle type
class VehicleType(models.Model):
    filter = models.CharField(max_length=12, null=True, blank=True)
    type = models.CharField(max_length=32)
    type_description = models.TextField(default="description")

    def __str__(self):
        return str(self.type)


# Vehicle purchase type
class VehiclePurchaseType(models.Model):
    purchase_type = models.CharField(max_length=32)
    purchase_description = models.TextField(default="description")

    def __str__(self):
        return str(self.purchase_type)


# Vehicle status
class VehicleStatus(models.Model):
    vehicle_status = models.CharField(max_length=32)
    vehicle_status_description = models.TextField(default="description")

    def __str__(self):
        return str(self.vehicle_status)


# Rig type
class RigType(models.Model):
    rig_type = models.CharField(max_length=32)
    rig_type_description = models.TextField(default="description")

    def __str__(self):
        return str(self.rig_type)


# Budget model
class BudgetModel(models.Model):
    budget_model = models.CharField(max_length=32)
    budget_model_description = models.TextField(default="description")

    def __str__(self):
        return str(self.budget_model)


# Budget group
class BudgetGroup(models.Model):
    budget_model = models.ForeignKey(BudgetModel)
    group_name = models.CharField(max_length=20)
    group_description = models.TextField(default="description")
    group_perma_key = models.CharField(max_length=20, null=True, blank=True, unique=True)
    group_list_order = models.IntegerField(default=0)

    def __str__(self):
        return str(self.group_name)


# Budget category
class BudgetCategory(models.Model):
    budget_group = models.ForeignKey(BudgetGroup)
    category = models.CharField(max_length=50)
    parent_category = models.ForeignKey("self", null=True, blank=True)
    category_perma_key = models.CharField(max_length=20, null=True, blank=True, unique=True)

    def __str__(self):
        return str(self.category)


# Google place types
class GooglePlaceType(models.Model):
    created_at = models.DateTimeField(default=timezone.now, blank=True)
    type = models.CharField(max_length=50)

    class meta:
        ordering = ['type']

    def __str__(self):
        return self.type


# Google place detail
class GooglePlaceDetail(models.Model):
    created_at = models.DateTimeField(default=timezone.now, blank=True)
    place_id = models.CharField(max_length=256)
    place_name = models.CharField(max_length=256)
    place_types = models.CharField(max_length=1024)

    def __str__(self):
        return self.place_name


# Link google place types to categories
class CategorytoGoogleTypes(models.Model):
    category = models.ForeignKey(BudgetCategory)
    google_type = models.ForeignKey(GooglePlaceType)

    def __str__(self):
        return str(self.category)


# Satisfaction
class Satisfaction(models.Model):
    satisfaction_index = models.IntegerField()
    satisfaction_description = models.CharField(max_length=12)
    satisfaction_definition = models.TextField(default="definition")

    def __str__(self):
        return str(self.satisfaction_description)
