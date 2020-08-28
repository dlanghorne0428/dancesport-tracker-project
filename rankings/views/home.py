import datetime
from django.shortcuts import render, redirect
from comps.models.comp import Comp

def home(request):
    current_comps = Comp.objects.filter(end_date__gte=datetime.date.today())
    return render(request, 'rankings/home.html', {'current_comps': current_comps})


def scoring(request):
    return render(request, 'rankings/scoring.html')
