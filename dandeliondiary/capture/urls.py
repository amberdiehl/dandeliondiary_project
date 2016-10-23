from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^expenses', views.expenses, name="expenses"),
    url(r'^', views.new_expense, name="new_expense"),
]