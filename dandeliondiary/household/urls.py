from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^settings$', views.household_dashboard, name='household_dashboard'),
    url(r'^myinfo$', views.my_info, name='my_info'),
    url(r'^vehicles$', views.household_vehicles, name='maintain_vehicles'),
    url(r'^ajax/models-by-make/(?P<make_id>\d+)/$', views.ajax_models_by_make),
    url(r'^', views.household_profile, name='maintain_household'),
]