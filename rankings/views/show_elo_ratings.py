from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import DANCE_STYLE_CHOICES
from rankings.models.couple import Couple
from rankings.models.elo_rating import EloRating

#from operator import itemgetter


def show_elo_ratings(request, couple_type, dance_style):

    elo_ratings = EloRating.objects.filter(style=dance_style, couple__couple_type=couple_type, value__isnull=False).order_by('-value')
    if len(elo_ratings) == 0:
        return render(request, 'rankings/elo_ratings.html', {'dance_style': dance_style, 'couple_type': couple_type, 'error': "No Ratings Available"})

    style_label = elo_ratings[0].get_style_display()
    couple_type_label = elo_ratings[0].couple.get_couple_type_display()

    
    if request.method == "GET":
        last_name = request.GET.get('last_name')
        page_number = request.GET.get('page')
    else:
        page_number = 1
        url_string = request.path
        last_name = request.POST.get('last_name')
        if last_name is not None:
            url_string += "?last_name=" + last_name  
        return redirect(url_string)
        
    couple_data = list()
    index = 1
    for r in elo_ratings:
        couple_data.append({'index': index, 'rating': r})
        index += 1
    
    # filter for last name and paginate the rankings
    if last_name is not None:
        if len(last_name) > 0:
            couple_data = list(filter(lambda dancer: last_name.lower() in dancer['rating'].couple.dancer_1.name_last.lower()  or \
                                                     last_name.lower() in dancer['rating'].couple.dancer_2.name_last.lower(), couple_data))

    
    paginator = Paginator(couple_data, 16)
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/elo_ratings.html', {'page_obj': page_obj, 'dance_style': style_label, 'couple_type': couple_type_label})
