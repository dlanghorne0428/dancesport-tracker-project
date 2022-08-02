from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import DANCE_STYLE_CHOICES
from rankings.models.couple import Couple
from rankings.models.elo_rating import EloRating

#from operator import itemgetter


def show_elo_ratings(request, couple_type, dance_style):

    elo_ratings = EloRating.objects.filter(style=dance_style, couple__couple_type=couple_type, value__isnull=False).order_by('-value')

    style_label = elo_ratings[0].get_style_display()
    couple_type_label = elo_ratings[0].couple.get_couple_type_display()
    
    paginator = Paginator(elo_ratings, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/elo_ratings.html', {'page_obj': page_obj, 'dance_style': style_label, 'couple_type': couple_type_label})
