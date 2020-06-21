from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from rankings.models import Dancer, Couple
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

        teachers = Dancer.objects.filter(dancer_type="PRO")
        teacher_stats = list()
        for t in teachers:
            if Couple.objects.filter(couple_type="PAC").filter(dancer_2=t).count() > 0:
                stats = {'teacher': t, 'event_count': 0, 'total_points': Decimal(0.00), 'rating': Decimal(0.00), index: 0}
                teacher_stats.append(stats)

        possible_matching_entries = Heat_Entry.objects.filter(couple__couple_type="PAC").filter(heat__style=heat_style)
        for ts in teacher_stats:
            entries = possible_matching_entries.filter(couple__dancer_2=ts['teacher'])
            for e in entries:
                if e.points is not None:
                    ts['event_count'] += 1
                    ts['total_points'] += e.points
            if ts['event_count'] > 0:
                ts['total_points'] = round(ts['total_points'], 2)
                ts['rating'] = round(ts['total_points'] / ts['event_count'], 2)

        teacher_stats.sort(key=itemgetter('rating'), reverse=True)
        while teacher_stats[-1]['event_count'] == 0:
            teacher_stats.pop()
            if len(teacher_stats) == 0:
                break
        for i in range(len(teacher_stats)):
            teacher_stats[i]['index'] = i + 1

        cache.set(cache_key, teacher_stats)

    # filter by last name if necessary and paginate the results
    if last_name is not None:
        if len(last_name) > 0:
            teacher_stats = list(filter(lambda dancer: last_name.lower() in dancer['teacher'].name_last.lower(), teacher_stats))

    paginator = Paginator(teacher_stats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/calc_teacher_rankings.html', {'page_obj': page_obj, 'styles': style_labels, 'selected_style': style})
