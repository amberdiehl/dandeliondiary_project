from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^terms$', views.terms, name='terms'),
    url(r'^', views.home, name='home'),
]
