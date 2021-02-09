from django.shortcuts import render, redirect, get_object_or_404
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.forms import HeatForm


def edit_heat(request, heat_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    heat = get_object_or_404(Heat, pk=heat_id)
    comp_id = heat.comp_id
    if request.method == "GET":
        form = HeatForm(instance=heat)
        return render(request, 'comps/edit_heat.html', {'heat': heat, 'form': form})
    else: # POST
        submit = request.POST.get("submit")
        if submit == "Save":
            try:
                form = HeatForm(request.POST, instance=heat)
                form.save()
                return redirect('comps:comp_heats', comp_id)
            except ValueError:
                return render(request, 'comps/edit_heat.html', {'heat': heat, 'form': form, 'error': "Invalid data submitted."})
        elif submit == "Delete Heat":
            print("Deleting " + str(heat) + " " + heat.info)
            heat.delete()
            return redirect ('comps:comp_heats', comp_id)
