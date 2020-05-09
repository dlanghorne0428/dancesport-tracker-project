from django.urls import path
from . import views

app_name = 'comps'

urlpatterns = [
    path('', views.all_comps, name="all_comps"),
    path('<int:comp_id>/', views.comp_detail, name="comp_detail"),
    path('<int:comp_id>/heats', views.comp_heats, name="comp_heats"),
    path('<int:comp_id>/heats/<int:dancer_id>', views.dancer_heats, name="dancer_heats"),
    path('<int:comp_id>/dancers', views.dancers, name="dancers"),
    path('<int:comp_id>/load_dancers', views.load_dancers, name="load_dancers"),
    path('<int:comp_id>/resolve_dancers', views.resolve_dancers, name="resolve_dancers"),
    path('<int:comp_id>/load_heats', views.load_heats, name="load_heats"),
    path('<int:comp_id>/mismatch_heats', views.resolve_mismatches, name="resolve_mismatches"),
    path('<int:comp_id>/mismatch_heats/<int:wider_search>', views.resolve_mismatches, name="resolve_mismatches"),
    path('<int:comp_id>/combine_heats', views.combine_heats, name="combine_heats"),
    path('<int:comp_id>/null_entries', views.fix_null_entries, name="fix_null_entries"),
    path('<int:comp_id>/duplicate_entries', views.fix_dup_entries, name="fix_dup_entries"),
    path('<int:comp_id>/bad_couple_type', views.fix_couple_type, name="fix_couple_type"),
    path('<int:comp_id>/bad_couple_type/<int:count>', views.fix_couple_type, name="fix_couple_type"),
    path('heat/<int:heat_id>/', views.heat, name="heat"),
    path('heat_entry/<int:entry_id>/', views.edit_heat_entry, name="edit_heat_entry"),
    path('<int:comp_id>/load_scoresheets', views.load_scoresheets, name="load_scoresheets"),
    path('create/', views.createcomp, name='createcomp'),
]
