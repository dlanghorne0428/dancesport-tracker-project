from django.shortcuts import render, redirect, get_object_or_404
from comps.models import Heat, HeatEntry
from comps.forms import HeatForm


def heat(request, heat_id):
    heat = get_object_or_404(Heat, pk=heat_id)
    entries = HeatEntry.objects.filter(heat=heat)
    if entries.count() > 0:
        if entries.first().points is not None:
            entries = entries.order_by('-points')
        else:
            entries = entries.order_by('shirt_number')
    comp_id = heat.comp_id
    if request.method == "GET":
        form = HeatForm(instance=heat)
        return render(request, 'comps/heat.html', {'heat': heat, 'form': form, 'entries': entries})
    else:
        try:
            form = HeatForm(request.POST, instance=heat)
            form.save()
            return redirect('comps:comp_heats', comp_id)
        except ValueError:
            return render(request, 'comps/heat.html', {'heat': heat, 'form': form, 'error': "Invalid data submitted."})
