"""dandeliondiary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from . import views

urlpatterns = [
    url(r'^public/', include('public.urls', namespace='public')),
    url(r'^account/', include('account.urls')),
    url(r'^capture/', include('capture.urls', namespace='capture')),
    url(r'^household/', include('household.urls', namespace='household')),
    url(r'^compare/', include('compare.urls', namespace='compare')),
    url(r'^admin/', admin.site.urls),
    url(r'^', view=views.launch_homepage),
]

urlpatterns += staticfiles_urlpatterns()
