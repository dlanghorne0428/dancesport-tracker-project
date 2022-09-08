import datetime
from datetime import timedelta
from django.db.models import Q
from django.shortcuts import render, redirect
from comps.models.comp import Comp

def home(request):
    current_comps = list()
    #active_comps = Comp.objects.exclude(location='CANCELED')
    #current_comps = active_comps.exclude(start_date__gt=datetime.date.today()).exclude(end_date__lt=datetime.date.today() - timedelta(days=2)).order_by('start_date') 

    print("Test - can you see this?", flush=True)
    return render(request, 'rankings/home.html', {'current_comps': current_comps})


def scoring(request):
    return render(request, 'rankings/scoring.html')
