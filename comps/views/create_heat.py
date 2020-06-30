from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.forms import HeatForm
from rankings.models import Couple


def create_heat(request, comp_id, couple_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)
    couple = get_object_or_404(Couple, pk=couple_id)

    if request.method == "GET":
        form = HeatForm()
        return render(request, 'comps/create_heat.html', {'comp': comp, 'couple': couple, 'form': form})
    else: # POST
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                heat = Heat()
                heat.comp = comp
                heat.set_time("12:00pm", "") # use first day of comp
                form = HeatForm(request.POST, instance=heat)
                heat_instance = form.save()
                heat_entry = Heat_Entry()
                heat_entry.heat = heat_instance
                heat_entry.couple = couple
                heat_entry_instance = heat_entry.save()
                return redirect('comps:couple_heats', comp.id, couple.id)
            except ValueError:
                return render(request, 'comps/create_heat.html', {'comp': comp, 'form': form, 'error': "Invalid data submitted."})
