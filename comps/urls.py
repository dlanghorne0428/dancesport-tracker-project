from django.urls import path
from . import views

app_name = 'comps'

urlpatterns = [
    path('', views.all_comps, name="all_comps"),
    path('<int:comp_id>/', views.detail, name="detail"),
    path('view_heats/<int:comp_id>/', views.view_heats, name="view_heats"),
    path('heat_results/<int:heat_id>/', views.heat_results, name="heat_results"),
    path('create/', views.createcomp, name='createcomp'),
    path('process_heatlists/<int:comp_id>/', views.process_heatlists, name="process_heatlists"),
    path('celerytest/', views.celerytest, name='celerytest'),
]
