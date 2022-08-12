from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from rankings.models.couple import Couple


def fix_dup_entries(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)
    heats_in_comp = Heat.objects.filter(comp=comp).order_by('heat_number')
    for heat in heats_in_comp:
        entries = Heat_Entry.objects.filter(heat=heat).order_by('shirt_number')
        for e in entries:
            dup_entries = entries.filter(couple=e.couple)
            if dup_entries.count() > 1:
                if request.method == "GET":
                    #print(heat.category, heat.heat_number, heat.info, e.shirt_number)
                    return render(request, 'comps/fix_entries.html', {'heat': heat, 'entries': entries, 'targeted_entry': e})
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
