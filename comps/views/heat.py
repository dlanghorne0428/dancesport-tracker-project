from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.models.heatlist_error import Heatlist_Error
from comps.forms import HeatForm
from rankings.rating_stats import couple_stats


def heat(request, heat_id):
    # only show edit button for valid users
    show_edit_button = request.user.is_superuser

    heat = get_object_or_404(Heat, pk=heat_id)

    # get all heats that match this time of day
    parallel_heats = Heat.objects.filter(comp=heat.comp).filter(time=heat.time).order_by('heat_number', 'extra', 'info')
    heat_data = list()

    for h in parallel_heats:
        results_available = False
        errors = Heatlist_Error.objects.filter(heat=h)
        if len(errors) > 0:
            error = errors.first()
        else:
            error = None
        entries = Heat_Entry.objects.filter(heat=h)
        if entries.count() > 0:
            if entries.first().points is not None:
                entries = entries.order_by('-points')
                results_available = True
            else:
                for e in entries:
                    if h.style is None or h.style == Heat.UNKNOWN:
                        stats = couple_stats(e.couple)
                    else:
                        stats = couple_stats(e.couple, h.style)
                    e.rating = stats['rating']
                    e.save()
                entries = entries.order_by('-rating', 'shirt_number')

        next_item = {'heat': h, 'entries': entries, 'results_available': results_available, 'error': error}
        heat_data.append(next_item)

    comp_id = heat.comp_id

    # find the previous and next heats
    prev_heat_id = None
    prev_heat_time = None
    next_heat_id = None
    next_heat_time = None

    comp_heats = Heat.objects.filter(comp=heat.comp)

    for h in comp_heats:
        if h.time > heat.time:
            if next_heat_id is None or h.time < next_heat_time:
                next_heat_id = h.pk
                next_heat_time = h.time
        elif h.time < heat.time:
            if prev_heat_id is None or h.time > prev_heat_time:
                prev_heat_id = h.pk
                prev_heat_time = h.time


    return render(request, 'comps/heat.html', {'comp': heat.comp, 'heat_data': heat_data, 'prev_heat_id': prev_heat_id, 'next_heat_id': next_heat_id, 'show_edit_button': show_edit_button})
