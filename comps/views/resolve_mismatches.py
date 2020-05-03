from django.shortcuts import render, redirect, get_object_or_404
from comps.models import Comp, Heat, HeatEntry, UnmatchedHeatEntry, HeatlistDancer
from rankings.models import Couple
from rankings.couple_matching import find_couple_partial_match


def resolve_mismatches(request, comp_id):
    unmatched_entries = UnmatchedHeatEntry.objects.all().order_by('entry')
    comp = get_object_or_404(Comp, pk=comp_id)
    if unmatched_entries.count() == 0:
        # all unmatched entries resolved, delete heatlist_dancer entries from database
        heatlist_dancers = HeatlistDancer.objects.all().delete()
        comp.process_state = comp.HEAT_ENTRIES_MATCHED
        comp.save()
        return redirect("comps:comp_heats", comp_id)
    else:
        first_unmatched = unmatched_entries.first()
        print(unmatched_entries)
        possible_matches = find_couple_partial_match(first_unmatched.dancer, first_unmatched.partner)
        if request.method == "GET":
            possible_couples = list()
            for i in range(len(possible_matches)):
                possible_couples.append(possible_matches[i][0])
            return render(request, "comps/resolve_mismatches.html", {'comp':comp, 'first_entry': first_unmatched,
                                                                     'possible_matches': possible_couples,
                                                                     'couple_type': first_unmatched.entry.heat.couple_type(),
                                                                     'entries_remaining': unmatched_entries.count()})
        else: # POST
            submit = request.POST.get("submit")
            if submit == "Reset":
                return redirect('comps:heats', comp_id)
            elif submit == "Submit":
                couple_str = request.POST.get("couple")
                for pm_couple, pm_code in possible_matches:
                    if str(pm_couple) == couple_str:
                        similar_unmatched = UnmatchedHeatEntry.objects.filter(dancer=first_unmatched.dancer, partner=first_unmatched.partner)
                        for e in similar_unmatched:
                            # update the heat entry with the selected couple
                            e.entry.couple = pm_couple
                            e.entry.code = pm_code
                            print(e.entry)
                            e.entry.save()
                            e.delete()
                        break
                return redirect("comps:heat", first_unmatched.entry.heat.id)
            elif submit == "Delete":
                # deleting the heat entry that this unmatched entry points to will also delete all the unmatched entries
                # that point to the same entry.
                first_unmatched.entry.delete()
                return redirect("comps:heat", first_unmatched.entry.heat.id)