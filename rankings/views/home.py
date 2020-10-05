import datetime
from datetime import timedelta
from django.shortcuts import render, redirect
from comps.models.comp import Comp

def home(request):
    current_comps = Comp.objects.filter(start_date__gte=datetime.date.today() - timedelta(days=2)).filter(end_date__lte=datetime.date.today() + timedelta(days=5))
    return render(request, 'rankings/home.html', {'current_comps': current_comps})


def scoring(request):
    return render(request, 'rankings/scoring.html')
