from django.shortcuts import render, redirect, get_object_or_404
from comps.models import Comp, Heat, HeatEntry
from rankings.models import Couple


def fix_null_entries(request, comp_id):
    comp = get_object_or_404(Comp, pk=comp_id)
    heats_in_comp = Heat.objects.filter(comp=comp).order_by('heat_number')
    current_heat_number = 0
    for heat in heats_in_comp:
        entries = HeatEntry.objects.filter(heat=heat).order_by('shirt_number')
        for e in entries:
            if e.couple is None:
                if request.method == "GET":
                    print(heat.category, heat.heat_number, heat.info, e.shirt_number)
                    return render(request, 'comps/fix_null_entries.html', {'heat': heat, 'entries': entries, 'targeted_entry': e})
                else: #POST
                    submit = request.POST.get("submit")
                    if submit == "Skip":
                        return redirect ('comps:heat', heat.id)
                    elif submit == "Delete Entry":
                        e.delete()
                        if len(entries) == 1:
                            print("deleted only entry in this heat, deleting heat")
                            heat.delete()
                            return redirect ('comps:comp_heats', comp_id)
                        else:
                            return redirect('comps:heat', heat.id)
    else:
        return redirect ('comps:comp_heats', comp_id)
