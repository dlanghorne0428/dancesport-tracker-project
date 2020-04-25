from django.urls import path
from . import views

app_name = 'comps'

urlpatterns = [
    path('', views.all_comps, name="all_comps"),
    path('<int:comp_id>/', views.detail, name="detail"),
    path('<int:comp_id>/heats', views.heats, name="heats"),
    path('<int:comp_id>/load_dancers', views.load_dancers, name="load_dancers"),
    path('<int:comp_id>/dancers', views.resolve_dancers, name="resolve_dancers"),
    path('<int:comp_id>/load_heats', views.load_heats, name="load_heats"),
    path('<int:comp_id>/mismatch_heats', views.resolve_mismatches, name="resolve_mismatches"),
    path('heat_entries/<int:heat_id>/', views.heat_entries, name="heat_entries"),
    path('create/', views.createcomp, name='createcomp'),
]
