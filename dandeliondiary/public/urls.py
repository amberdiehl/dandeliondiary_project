from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^capture$', views.capture, name='capture'),
    url(r'^compare$', views.compare, name='compare'),
    url(r'^contribute$', views.contribute, name='contribute'),
    url(r'^terms$', views.terms, name='terms'),
    url(r'^privacy$', views.privacy, name='privacy'),
    url(r'^cookies$', views.cookies, name='cookies'),
    url(r'^', views.home, name='home'),
]
