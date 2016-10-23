from django.contrib import admin
from models import *

# Register your models here.
admin.site.register(Household)
admin.site.register(RVHousehold)
admin.site.register(Member)
admin.site.register(HouseholdMembers)
admin.site.register(Payment)

admin.site.register(Vehicle)