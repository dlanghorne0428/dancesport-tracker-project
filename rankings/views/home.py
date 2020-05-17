from django.shortcuts import render, redirect
from rankings.models import Couple
from comps.models import Heat


def home(request):
    couple_types = Couple.COUPLE_TYPE_CHOICES
    heat_couple_type = couple_types[0][0]
    styles = Heat.DANCE_STYLE_CHOICES
    heat_style = styles[0][0]

    url_string = "rankings/?type=" + heat_couple_type + "&style=" + heat_style
    return redirect(url_string)
