from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import DANCE_STYLE_CHOICES
from rankings.forms import EloRatingForm
from rankings.models.couple import Couple
from rankings.models.elo_rating import EloRating

#from operator import itemgetter


def show_elo_ratings(request):
    
    couple_types = Couple.COUPLE_TYPE_CHOICES
    couple_type_choices = list()
    for c in couple_types:
        couple_type_choices.append(c[0])
    couple_type_labels = list()
    for c in couple_types:
        couple_type_labels.append(c[1])

    styles = DANCE_STYLE_CHOICES
    style_choices = list()
    for s in styles:
        style_choices.append(s[0])
    style_labels = list()
    for s in styles:
        style_labels.append(s[1])

    if request.method == "GET":
        page_number = request.GET.get('page')
        heat_couple_type = request.GET.get('type')
        if heat_couple_type is None:
            heat_couple_type = "PRC"
        index = couple_type_choices.index(heat_couple_type)
        couple_type = couple_type_labels[index]

        heat_style = request.GET.get('style')
        if heat_style is None:
            heat_style = "SMOO"
        index = style_choices.index(heat_style)
        style = style_labels[index]

        last_name = request.GET.get('last_name') 
        
    else:
        page_number = 1
        couple_type_index = int(request.POST.get("couple_type"))
        #index = couple_type_labels.index(couple_type)
        heat_couple_type = Couple.COUPLE_TYPE_CHOICES[couple_type_index][0]
        style = request.POST.get("style")
        index = style_labels.index(style)
        heat_style = DANCE_STYLE_CHOICES[index][0]
        current_url = request.path
        url_string = current_url +"?type=" + heat_couple_type + "&style=" + heat_style
        last_name = request.POST.get("last_name")
        if last_name is not None:
            url_string += "&last_name=" + last_name
        return redirect(url_string)

    elo_ratings = EloRating.objects.filter(style=heat_style, couple__couple_type=heat_couple_type, value__isnull=False).order_by('-value')

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
    return render(request, 'rankings/elo_ratings.html', {'page_obj': page_obj, 'styles': style_labels, 'selected_style': style,
                                                         'couple_types': couple_type_labels, 'selected_couple_type': couple_type})


def edit_elo_ratings(request, couple_pk,  dance_style):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    
    couple = get_object_or_404(Couple, pk=couple_pk)
    elo_rating = EloRating.objects.get(couple=couple, style=dance_style)
    
    if request.method == "GET":
        form = EloRatingForm(instance=elo_rating)
        return render(request, 'rankings/edit_elo_rating.html', {'rating': elo_rating, 'form': form})
    else:
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = EloRatingForm(data=request.POST,instance=elo_rating)
                form.save()
                return redirect('view_couple', couple_pk)
            except ValueError:
                return render(request, 'rankings/edit_elo_rating.html', {'rating': elo_rating, 'form': form, 'error': "Invalid data submitted."})
        else:
            return redirect('view_couple', couple_pk)      