from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^new', views.new_expense, name="new_expense"),
    url(r'^explore', views.explore_expenses, name="explore_expenses"),
    url(r'^reconcile', views.reconcile_expenses, name="reconcile_expenses"),
    url(r'^tags', views.maintain_tags, name="maintain_tags"),
    url(r'^payees', views.maintain_payee_associations, name="maintain_payee_associations"),
    url(r'^export', views.export_expenses_to_csv, name="export_expenses"),
    url(r'^ajax/places/(?P<lat>[0-9.\-]+)/(?P<lon>[0-9.\-]+)/$', views.ajax_categories_by_place),
    url(r'^ajax/list_expenses/$', views.ajax_list_expenses),
    url(r'^ajax/change_expense/(?P<s>[d|u])/$', views.ajax_change_expense),
    url(r'^ajax/add_quick_expense/$', views.ajax_expense_quick_add),
]