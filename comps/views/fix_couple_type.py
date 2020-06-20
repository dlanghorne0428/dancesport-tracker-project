from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from rankings.models import Couple


def fix_couple_type(request, comp_id, count=0):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')

    comp = get_object_or_404(Comp, pk=comp_id)
    heats_in_comp = Heat.objects.filter(comp=comp).order_by('heat_number')
    findings = 0
    for heat in heats_in_comp:
        heat_couple_type = heat.couple_type()
        entries = Heat_Entry.objects.filter(heat=heat).order_by('shirt_number')
        for e in entries:
            if e.couple is not None:
                if e.couple.couple_type != heat_couple_type:
                    findings += 1
                    if findings > count:
                        matching_couples = Couple.objects.filter(dancer_1=e.couple.dancer_1).order_by('dancer_2')
                        if request.method == "GET":
                            return render (request, 'comps/fix_couple_type.html', {'heat': heat, 'heat_couple_type': heat_couple_type, \
                                                                             'entries': entries, 'targeted_entry': e, \
                                                                             'matching_couples': matching_couples})
                        else: #POST
                            submit = request.POST.get("submit")
                            if submit == "Skip":
                                return redirect ('comps:fix_couple_type', comp_id, count+1)
                            elif submit == "Change Couple":
                                # replace the couple in this heat entry with the selected couple
                                couple_str = request.POST.get("couple")
                                for mc in matching_couples:
                                    if str(mc) == couple_str and mc.couple_type == heat_couple_type:
                                        print("Found match: ", mc.dancer_1, mc.dancer_2, mc.couple_type)
                                        e.couple = mc
                                        e.save()
                                        return redirect ('comps:fix_couple_type', comp_id, count)
                            elif submit == "Change Type":
                                # change the type of the existing couple in this heat entry
                                e.couple.couple_type = heat_couple_type
                                e.couple.save()
                                return redirect('comps:heat', heat.id)
    else:
        return redirect ('comps:comp_heats', comp_id)
