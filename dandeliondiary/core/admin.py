from django.contrib import admin
from django import forms
from models import *

admin.site.site_header = "Dandelion Diary Administration"

# Register your models here.
admin.site.register(IncomeType)
admin.site.register(UseType)
admin.site.register(RigType)

class VehicleModelInline(admin.TabularInline):
    model = VehicleModel


class VehicleMakeAdmin(admin.ModelAdmin):
    inlines = [
        VehicleModelInline,
    ]
admin.site.register(VehicleMake, VehicleMakeAdmin)

admin.site.register(VehicleType)
admin.site.register(VehiclePurchaseType)
admin.site.register(VehicleStatus)


# Enable creation of budget groups within a buget model
class BudgetGroupInline(admin.TabularInline):
    list_display = ('group_name', 'group_description', 'group_perma_key', 'group_list_order', )
    ordering = ('group_list_order', )
    model = BudgetGroup


class BudgetModelAdmin(admin.ModelAdmin):
    inlines = [
        BudgetGroupInline,
    ]

admin.site.register(BudgetModel, BudgetModelAdmin)

class BudgetCategoryInline(admin.TabularInline):
    model = BudgetCategory
    ordering = ('parent_category', 'category', )


class BudgetGroupAdmin(admin.ModelAdmin):
    inlines = [
        BudgetCategoryInline,
    ]

admin.site.register(BudgetGroup, BudgetGroupAdmin)


class CategorytoGoogleTypesForm(forms.ModelForm):
    google_type = forms.ModelChoiceField(queryset=GooglePlaceType.objects.order_by('type'))

    class Meta:
        model = CategorytoGoogleTypes
        fields = ('category', 'google_type',)


class CategorytoGoogleTypesInline(admin.TabularInline):
    list_display = ('category', 'google_type', )
    form = CategorytoGoogleTypesForm
    model = CategorytoGoogleTypes


class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ('budget_group', 'category', 'parent_category', )
    ordering = ('budget_group', 'parent_category', 'category', )
    inlines = [
        CategorytoGoogleTypesInline,
    ]

admin.site.register(BudgetCategory, BudgetCategoryAdmin)

admin.site.register(GooglePlaceType)

admin.site.register(GooglePlaceDetail)


class CategorytoGoogleTypesAdmin(admin.ModelAdmin):
    list_display = ('google_type', 'category', )
    ordering = ('google_type', )

admin.site.register(CategorytoGoogleTypes, CategorytoGoogleTypesAdmin)

admin.site.register(Satisfaction)