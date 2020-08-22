from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp 
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.forms import CompForm, HeatForm
from rankings.models import Couple


def combine_heats(request, comp_id):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)
    heats_in_comp = Heat.objects.filter(comp=comp).order_by('heat_number')
    current_heat_number = 0
    for heat in heats_in_comp:
        if heat.info_prefix() != heat.info:
            if heat.heat_number != current_heat_number:
                current_heat_number = heat.heat_number
                print("Processing Heat", current_heat_number)
                possible_matches = list()
            for match in possible_matches:
                if heat.info_prefix() == match.info_prefix():
                    if request.method == "GET":
                        print("Found ", heat.category, heat.heat_number, heat.info)
                        print("Match!", match.category, match.heat_number, match.info)
                        return render(request, 'comps/combine_heats.html', {'heats': (heat, match)})
                    else:  # POST
                        submit = request.POST.get("submit")
                        if submit == "Skip":
                            return redirect ('comps:heat', heat.id)
                        elif submit == "Submit":
                            heat.remove_info_prefix()
                            print("Combine", heat.category, heat.heat_number, heat.info)
                            heat.save()
                            matching_entries = Heat_Entry.objects.filter(heat=match).order_by('shirt_number')
                            for e in matching_entries:
                                print(e.couple, e.code, e.shirt_number)
                                e.heat = heat
                                print(e.heat.info)
                                e.save()
                            match.delete()
                            return redirect ('comps:heat', heat.id)
            else:
                possible_matches.append(heat)

    return redirect ('comps:comp_heats', comp_id)
