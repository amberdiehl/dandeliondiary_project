from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^settings$', views.household_dashboard, name='household_dashboard'),
    url(r'^myinfo$', views.my_info, name='my_info'),
    url(r'^profile$', views.household_profile, name='maintain_household'),
    url(r'^members$', views.household_members, name='maintain_members'),
    url(r'^vehicles$', views.household_vehicles, name='maintain_vehicles'),
    url(r'^ajax/models-by-make/(?P<make_id>\d+)/$', views.ajax_models_by_make),
    url(r'^ajax/makes-by-type/(?P<type_id>\d+)/$', views.ajax_makes_by_type),
    url(r'^ajax/add-make/(?P<type_key>\d+)/(?P<make>[\w ]{1,50})/$', views.ajax_add_make),
    url(r'^ajax/add-model/(?P<make_key>\d+)/(?P<model>[\w -]{1,128})/$', views.ajax_add_model),
    url(r'^ajax/delete-invite/$', views.ajax_delete_invite),
    url(r'^ajax/change-member-status/$', views.ajax_change_member_status),
]
