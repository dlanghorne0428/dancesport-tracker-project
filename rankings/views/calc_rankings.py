from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from rankings.models import Dancer, Couple
from comps.models.comp import Comp
from comps.models.heat import Heat
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

    styles = Heat.DANCE_STYLE_CHOICES
    style_choices = list()
    for s in styles:
        style_choices.append(s[0])
    style_labels = list()
    for s in styles:
        style_labels.append(s[1])

    if request.method == "GET":
        page_number = request.GET.get('page')
        print("Page Number is", page_number)
        heat_couple_type = request.GET.get('type')
        index = couple_type_choices.index(heat_couple_type)
        couple_type = couple_type_labels[index]
        print("Couple_Type is", heat_couple_type, couple_type)
        heat_style = request.GET.get('style')
        index = style_choices.index(heat_style)
        style = style_labels[index]
        print("Style is", heat_style, style)
        last_name = request.GET.get('last_name')
        print("Last name is", last_name)
    else:
        page_number = 1
        couple_type = request.POST.get("couple_type")
        index = couple_type_labels.index(couple_type)
        heat_couple_type = Couple.COUPLE_TYPE_CHOICES[index][0]
        style = request.POST.get("style")
        index = style_labels.index(style)
        heat_style = Heat.DANCE_STYLE_CHOICES[index][0]
        current_url = request.path
        url_string = current_url +"?type=" + heat_couple_type + "&style=" + heat_style
        last_name = request.POST.get("last_name")
        if last_name is not None:
            url_string += "&last_name=" + last_name
        print("POST", url_string)
        return redirect(url_string)

    couples = Couple.objects.filter(couple_type=heat_couple_type)
    couple_stats = list()
    for c in couples:
        stats = {'couple': c, 'event_count': 0, 'total_points': 0.0, 'rating': 0.0, index: 0}
        couple_stats.append(stats)

    for cs in couple_stats:
        entries = Heat_Entry.objects.filter(couple=cs['couple']).filter(heat__style=heat_style)
        for e in entries:
            if e.points is not None:
                cs['event_count'] += 1
                cs['total_points'] += e.points
        if cs['event_count'] > 0:
            cs['total_points'] = round(cs['total_points'], 2)
            cs['rating'] = round(cs['total_points'] / cs['event_count'], 2)

    couple_stats.sort(key=itemgetter('rating'), reverse=True)
    while couple_stats[-1]['event_count'] == 0:
        couple_stats.pop()
        if len(couple_stats) == 0:
            break
    for i in range(len(couple_stats)):
        couple_stats[i]['index'] = i + 1
    if last_name is not None:
        if len(last_name) > 0:
            couple_stats = list(filter(lambda dancer: last_name.lower() in dancer['couple'].dancer_1.name_last.lower()  or \
                                                      last_name.lower() in dancer['couple'].dancer_2.name_last.lower(), couple_stats))
    paginator = Paginator(couple_stats, 16)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'rankings/calc_rankings.html', {'page_obj': page_obj, 'styles': style_labels, 'selected_style': style,
                                                      'couple_types': couple_type_labels, 'selected_couple_type': couple_type})
