from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^dashboard/$', views.compare_dashboard, name='compare_dashboard'),
    url(r'^groups_categories/$', views.groups_and_categories, name='groups_categories'),
    url(r'^budget/$', views.budget, name='budget'),
    url(r'^budgets_expenses/$', views.budget_and_expenses, name='budgets_expenses'),
    url(r'^ajax/dashboard_snapshot/(?P<dt>\d{4}-\d{2}-\d{2})/$', views.ajax_dashboard_snapshot),
    url(r'^ajax/dashboard_month_series/(?P<from_date>\d{4}-\d{2}-\d{2})/(?P<to_date>\d{4}-\d{2}-\d{2})/$',
        views.ajax_dashboard_month_series),
    url(r'^ajax/dashboard_budget/(?P<dt>\d{4}-\d{2}-\d{2})/$', views.ajax_dashboard_budget),
    url(r'^ajax/list_groups/$', views.ajax_list_groups),
    url(r'^ajax/create_group/$', views.ajax_create_group),
    url(r'^ajax/update_group/$', views.ajax_update_group),
    url(r'^ajax/delete_group/$', views.ajax_delete_group),
    url(r'^ajax/list_categories/(?P<s>\w)/(?P<pid>\w{16})/$', views.ajax_list_categories),
    url(r'^ajax/create_category/(?P<pid>\w{16})/$', views.ajax_create_category),
    url(r'^ajax/update_category/$', views.ajax_update_category),
    url(r'^ajax/delete_category/$', views.ajax_delete_category),
    url(r'^ajax/create_child_category/(?P<pid>\w{16})/$', views.ajax_create_child_category),
    url(r'^ajax/list_budgets/(?P<pid>\w{16})/$', views.ajax_list_budgets),
    url(r'^ajax/create_budget/(?P<pid>\w{16})/$', views.ajax_create_budget),
    url(r'^ajax/change_budget/(?P<s>\w)/$', views.ajax_change_budget),
    url(r'^ajax/budget_summary/$', views.ajax_budget_summary),
    url(r'^ajax/be_groups/(?P<dt>\d{4}-\d{1,2}-\d{1,2})/$', views.ajax_be_groups),
    url(r'^ajax/be_categories/(?P<pid>\w{16})/(?P<dt>\d{4}-\d{1,2}-\d{1,2})/$', views.ajax_be_categories),
]
