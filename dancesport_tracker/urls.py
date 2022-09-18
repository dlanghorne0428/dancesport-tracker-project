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
    path('login/', views.loginuser, name="loginuser"),
    path('logout/', views.logoutuser, name="logoutuser"),
    path('elo/', views.show_elo_ratings, name="show_elo_ratings"),
    path('elo_recalc/', views.recalc_elo_ratings, name="recalc_elo_ratings"),
    path('elo_edit/<int:couple_pk>/<str:dance_style>', views.edit_elo_ratings, name="edit_elo_ratings"),
    #path('rankings/', views.calc_rankings, name="calc_rankings"),
    #path('rankings/teachers', views.calc_teacher_rankings, name="calc_teacher_rankings"),
    path('scoring', views.scoring, name="scoring"),
    path('dancers/', views.all_dancers, name="all_dancers"),
    path('dancers/alias_list/<int:level>/', views.alias_dancers, name="alias_dancers"),
    path('dancers/alias/<int:hld_pk>/', views.aliases_for_dancer, name="aliases_for_dancer"),
    path('dancers/accept_alias/<int:hld_pk>', views.accept_alias, name="accept_alias"),
    path('dancers/reject_alias/<int:hld_pk>', views.reject_alias, name="reject_alias"),
    path('dancers/<int:dancer_pk>', views.view_dancer, name='view_dancer'),
    path('dancers/edit/<int:dancer_pk>', views.edit_dancer, name='edit_dancer'),
    path('dancers/create/', views.create_dancer, name='create_dancer'),
    path('dancers/create/<str:name_str>/<int:comp_pk>', views.create_dancer, name='create_dancer'),
    path('couples/', views.all_couples, name="all_couples"),
    path('couples/<int:couple_pk>', views.view_couple, name='view_couple'),
    path('couples/<int:couple_pk>/combine/<int:couple2_pk>', views.combine_couples, name='combine_couples'),
    path('couples/flip/<int:couple_pk>', views.flip_couple, name='flip_couple'),
    path('couples/delete/<int:couple_pk>', views.delete_couple, name='delete_couple'),
    path('couples/edit/<int:couple_pk>', views.edit_couple, name='edit_couple'),
    path('couples/change_type/<int:couple_pk>', views.change_couple_type, name='change_couple_type'),
    path('couples/create/', views.create_couple, name='create_couple'),
    path('couples/create/<str:couple_type>/<int:dancer_pk>/<int:dancer_position>/', views.create_couple, name='create_couple'),
    path('couples/create/<str:couple_type>/<int:dancer_pk>/<int:dancer_position>/<int:partner_pk>', views.create_couple, name='create_couple'),
    path('comps/', include('comps.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
