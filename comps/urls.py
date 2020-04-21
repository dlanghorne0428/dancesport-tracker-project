from django.urls import path
from . import views

app_name = 'comps'

urlpatterns = [
    path('', views.all_comps, name="all_comps"),
    path('<int:comp_id>/', views.detail, name="detail"),
    path('heats/<int:comp_id>/', views.heats, name="heats"),
    path('heat_entries/<int:heat_id>/', views.heat_entries, name="heat_entries"),
    path('create/', views.createcomp, name='createcomp'),
    path('process_heatlists/<int:comp_id>/', views.process_heatlists, name="process_heatlists"),
    path('resolve_mismatches/<int:comp_id>/', views.resolve_mismatches, name="resolve_mismatches"),
]
