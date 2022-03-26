from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from rankings.tasks import calc_teacher_ratings
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from operator import itemgetter
from decimal import Decimal


def calc_teacher_rankings(request):
    styles = Heat.DANCE_STYLE_CHOICES
    style_choices = list()
    for s in styles:
        style_choices.append(s[0])
    style_labels = list()
    for s in styles:
        style_labels.append(s[1])

    if request.method == "GET":
        page_number = request.GET.get('page')

        heat_style = request.GET.get('style')
        if heat_style is None:
            heat_style = "SMOO"
        index = style_choices.index(heat_style)
        style = style_labels[index]

        last_name = request.GET.get('last_name')

        cache_key = heat_style

    else:
        page_number = 1

        style = request.POST.get("style")
        index = style_labels.index(style)
        heat_style = Heat.DANCE_STYLE_CHOICES[index][0]

        current_url = request.path
        url_string = current_url + "?style=" + heat_style

        last_name = request.POST.get("last_name")
        if last_name is not None:
            url_string += "&last_name=" + last_name
        return redirect(url_string)

    teacher_stats = cache.get(cache_key)

    if teacher_stats is None:
        # cache miss - calculate rankings and store in cache
        result = calc_teacher_ratings.delay(heat_style, cache_key)
        return render(request, 'rankings/calc_teacher_ranking_progress.html', context={'task_id': result.task_id, 'styles': style_labels, 'selected_style': style})

    # filter by last name if necessary and paginate the results
    if last_name is not None:
        if len(last_name) > 0:
            teacher_stats = list(filter(lambda dancer: last_name.lower() in dancer['instructor'].name_last.lower(), teacher_stats))

    paginator = Paginator(teacher_stats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/calc_teacher_rankings.html', {'page_obj': page_obj, 'styles': style_labels, 'selected_style': style})
