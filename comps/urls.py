from django.urls import path
from . import views

app_name = 'comps'

urlpatterns = [
    path('', views.all_comps, name="all_comps"),
    path('<int:comp_id>/', views.detail, name="detail"),
    path('heatlists/<int:comp_id>/', views.process_heatlists, name="process_heatlists"),    
    path('create/', views.createcomp, name='createcomp'),
]
