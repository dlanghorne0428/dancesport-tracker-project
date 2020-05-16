from django.shortcuts import render, redirect, get_object_or_404
from comps.models import Heat, HeatEntry
from comps.forms import HeatForm


def heat(request, heat_id):
    # only show edit button for valid users
    show_edit_button = request.user.is_superuser

    heat = get_object_or_404(Heat, pk=heat_id)
    entries = HeatEntry.objects.filter(heat=heat)
    if entries.count() > 0:
        if entries.first().points is not None:
            entries = entries.order_by('-points')
        else:
            entries = entries.order_by('shirt_number')
    comp_id = heat.comp_id
    return render(request, 'comps/heat.html', {'heat': heat, 'entries': entries, 'show_edit_button': show_edit_button})
