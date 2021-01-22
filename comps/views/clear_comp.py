from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat

def clear_comp(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)

    # delete all the heats in the comps
    heats = Heat.objects.filter(comp=comp)
    for h in heats:
        h.delete()

    # reset the status for the next year's comp
    comp.process_state = Comp.INITIAL
    comp.save()

    # return to the list of comps
    return redirect("comps:all_comps")
