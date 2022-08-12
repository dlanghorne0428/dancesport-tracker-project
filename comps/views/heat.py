from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import Heat, UNKNOWN
from comps.models.heat_entry import Heat_Entry
from comps.models.heatlist_error import Heatlist_Error
from comps.models.result_error import Result_Error
from comps.forms import HeatForm
from rankings.rating_stats import couple_stats


def heat(request, heat_id, sort_mode=0):
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
            error = errors.first().get_error_display()
        else:
            error = None
        if error is None:
            errors = Result_Error.objects.filter(heat=h)
            if len(errors) > 0:
                error = errors.first().get_error_display()
                
        entries = Heat_Entry.objects.filter(heat=h)
        if entries.count() > 0:
            for e in entries:
                if e.points is not None:
                    entries = entries.order_by('-points')
                    results_available = True
                    break
            else:
                for e in entries:
                    if h.style is None or h.style == UNKNOWN:
                        stats = couple_stats(e.couple)
                    else:
                        stats = couple_stats(e.couple, h.style)
                    e.rating = stats['rating']
                    e.save()
                if sort_mode == 0:
                    entries = entries.order_by('-rating', 'shirt_number')
                elif sort_mode == 1:
                    entries = entries.order_by('rating', 'shirt_number')
                elif sort_mode == 2:
                    entries = entries.order_by('-shirt_number')
                elif sort_mode == 3:
                    entries = entries.order_by('shirt_number')
                elif sort_mode == 4:
                    entries = entries.order_by('-couple')
                elif sort_mode == 5:
                    entries = entries.order_by('couple')

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
