from django.urls import path
from . import views

app_name = 'comps'

urlpatterns = [
    path('', views.all_comps, name="all_comps"),
    path('<int:comp_id>/', views.comp_detail, name="comp_detail"),
    path('<int:comp_id>/heats', views.comp_heats, name="comp_heats"),
    path('<int:comp_id>/load_dancers', views.load_dancers, name="load_dancers"),
    path('<int:comp_id>/dancers', views.resolve_dancers, name="resolve_dancers"),
    path('<int:comp_id>/load_heats', views.load_heats, name="load_heats"),
    path('<int:comp_id>/mismatch_heats', views.resolve_mismatches, name="resolve_mismatches"),
    path('heat/<int:heat_id>/', views.heat, name="heat"),
    path('create/', views.createcomp, name='createcomp'),
]
