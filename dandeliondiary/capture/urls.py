from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^new', views.new_expense, name="new_expense"),
    url(r'^explore', views.explore_expenses, name="explore_expenses"),
    url(r'^ajax/list_expenses/$', views.ajax_list_expenses),
    url(r'^ajax/change_expense/(?P<s>[d|u])/$', views.ajax_change_expense),
]