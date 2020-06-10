from django.shortcuts import render, redirect



def home(request):
    return render(request, 'rankings/home.html')


def scoring(request):
    return render(request, 'rankings/scoring.html')
