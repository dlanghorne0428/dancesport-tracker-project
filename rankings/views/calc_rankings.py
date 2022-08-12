from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from rankings.models.couple import Couple
from rankings.tasks import calc_couple_ratings
from comps.models.comp import Comp
from comps.models.heat import Heat, DANCE_STYLE_CHOICES
from comps.models.heat_entry import Heat_Entry
from operator import itemgetter


def calc_rankings(request):
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

        cache_key = heat_couple_type + "-" + heat_style

    else:
        page_number = 1
        couple_type = request.POST.get("couple_type")
        index = couple_type_labels.index(couple_type)
        heat_couple_type = Couple.COUPLE_TYPE_CHOICES[index][0]
        style = request.POST.get("style")
        index = style_labels.index(style)
        heat_style = DANCE_STYLE_CHOICES[index][0]
        current_url = request.path
        url_string = current_url +"?type=" + heat_couple_type + "&style=" + heat_style
        last_name = request.POST.get("last_name")
        if last_name is not None:
            url_string += "&last_name=" + last_name
        return redirect(url_string)

    # try to read the ranking data from the cache
    couple_stats = cache.get(cache_key)
    

    if couple_stats is None:
        # cache miss - calculate rankings and store in cache
        result = calc_couple_ratings.delay(heat_couple_type, heat_style, cache_key)
        return render(request, 'rankings/calc_ranking_progress.html', context={'task_id': result.task_id, 'styles': style_labels, 'selected_style': style,
                                                          'couple_types': couple_type_labels, 'selected_couple_type': couple_type})

    # filter for last name and paginate the rankings
    if last_name is not None:
        if len(last_name) > 0:
            couple_stats = list(filter(lambda dancer: last_name.lower() in dancer['couple'].dancer_1.name_last.lower()  or \
                                                      last_name.lower() in dancer['couple'].dancer_2.name_last.lower(), couple_stats))
    paginator = Paginator(couple_stats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/calc_rankings.html', {'page_obj': page_obj, 'styles': style_labels, 'selected_style': style,
                                                      'couple_types': couple_type_labels, 'selected_couple_type': couple_type})
