"""dancesport_tracker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.conf import settings

from rankings import views

app_name = 'rankings'

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^celery-progress/', include('celery_progress.urls')),  # the endpoint is configurabl
    path('', views.home, name="home"),
    path('dancers/', views.all_dancers, name="all_dancers"),
    path('dancers/edit/<int:dancer_pk>', views.viewdancer, name='viewdancer'),
    path('dancers/create/', views.createdancer, name='createdancer'),
    path('couples/', views.all_couples, name="all_couples"),
    path('couples/edit/<int:couple_pk>', views.viewcouple, name='viewcouple'),
    path('couples/create/', views.createcouple, name='createcouple'),
    path('comps/', include('comps.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
