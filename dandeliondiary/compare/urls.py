from django.conf.urls import include, url
from . import views

urlpatterns = [
    url(r'^dashboard/$', views.compare_dashboard, name='compare_dashboard'),
    url(r'^groups_categories/$', views.groups_and_categories, name='groups_categories'),
    url(r'^budget/$', views.budget, name='budget'),
    url(r'^ajax/dash_budget/$', views.ajax_dash_budget),
    url(r'^ajax/list_groups/$', views.ajax_list_groups),
    url(r'^ajax/create_group/$', views.ajax_create_group),
    url(r'^ajax/update_group/$', views.ajax_update_group),
    url(r'^ajax/delete_group/$', views.ajax_delete_group),
    url(r'^ajax/list_categories/(?P<s>\w+)/(?P<pid>\w+)/?', views.ajax_list_categories),
    url(r'^ajax/create_category/(?P<pid>\w+)/?', views.ajax_create_category),
    url(r'^ajax/update_category/$', views.ajax_update_category),
    url(r'^ajax/delete_category/$', views.ajax_delete_category),
    url(r'^ajax/create_child_category/(?P<pid>\w+)/?', views.ajax_create_child_category),
    url(r'^ajax/list_budgets/(?P<pid>\w+)/?', views.ajax_list_budgets),
    url(r'^ajax/create_budget/(?P<pid>\w+)/?', views.ajax_create_budget),
    url(r'^ajax/change_budget/(?P<s>\w+)/?', views.ajax_change_budget),
    url(r'^ajax/budget_summary/$', views.ajax_budget_summary),
]
