from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.forms import HeatForm
from rankings.couple_stats import couple_stats


def heat(request, heat_id):
    # only show edit button for valid users
    show_edit_button = request.user.is_superuser

    heat = get_object_or_404(Heat, pk=heat_id)

    # get all heats that match this category and heat number
    parallel_heats = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number)
    heat_data = list()

    for h in parallel_heats:
        results_available = False
        entries = Heat_Entry.objects.filter(heat=h)
        if entries.count() > 0:
            if entries.first().points is not None:
                entries = entries.order_by('-points')
                results_available = True
            else:
                for e in entries:
                    stats = couple_stats(e.couple, h.style)
                    e.rating = stats['rating']
                    e.save()
                entries = entries.order_by('-rating')

        next_item = {'heat': h, 'entries': entries, 'results_available': results_available}
        heat_data.append(next_item)

    comp_id = heat.comp_id
    prev_heat = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number-1).first()
    if prev_heat is not None:
        prev_heat_id = prev_heat.id
    else:
        prev_heat_id = None
    next_heat = Heat.objects.filter(comp=heat.comp).filter(category=heat.category).filter(heat_number=heat.heat_number+1).first()
    if next_heat is not None:
        next_heat_id = next_heat.id
    else:
        next_heat_id = None
    return render(request, 'comps/heat.html', {'comp': heat.comp, 'heat_data': heat_data, 'prev_heat_id': prev_heat_id, 'next_heat_id': next_heat_id, 'show_edit_button': show_edit_button})
