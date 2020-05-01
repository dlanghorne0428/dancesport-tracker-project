from django.shortcuts import render, redirect, get_object_or_404
from comps.models import Comp, Heat, HeatEntry, UnmatchedHeatEntry, HeatlistDancer
from rankings.models import Couple


def resolve_mismatches(request, comp_id):
    unmatched_entries = UnmatchedHeatEntry.objects.all().order_by('entry')
    if request.method == "GET":
        comp = get_object_or_404(Comp, pk=comp_id)
        if unmatched_entries.count() == 0:
            # all unmatched entries resolved, delete heatlist_dancer entries from database
            heatlist_dancers = HeatlistDancer.objects.all().delete()
            comp.process_state = comp.HEAT_ENTRIES_MATCHED
            comp.save()
            return redirect("comps:comp_heats", comp_id)
        else:
            first_unmatched = unmatched_entries.first()
            first_set = unmatched_entries.filter(entry=first_unmatched.entry).order_by('couple__dancer_1')
            return render(request, "comps/resolve_mismatches.html", {'comp':comp, 'first_entry': first_unmatched, 'unmatched_entries': first_set,
                                                                     'couple_type': first_unmatched.entry.heat.couple_type()})
    else: # POST
        submit = request.POST.get("submit")
        if submit == "Reset":
            return redirect('comps:heats', comp_id)
        elif submit == "Submit":
            couple = request.POST.get("couple")
            first_entry = unmatched_entries.first()
            first_set = UnmatchedHeatEntry.objects.filter(dancer=first_entry.dancer, partner=first_entry.partner)
            for e in first_set:
                if str(e.couple) == couple:
                    # update the heat entry with the selected couple
                    e.entry.couple = e.couple
                    e.entry.code = e.code
                    e.entry.save()
                # delete the heat entries that have been resolved
                e.delete()
            return redirect("comps:heat", first_entry.entry.heat.id)
        elif submit == "Delete":
            first_entry = unmatched_entries.first()
            # deleting the heat entry that this unmatched entry points to will also delete all the unmatched entries
            # that point to the same entry.
            first_entry.entry.delete()
            return redirect("comps:heat", first_entry.entry.heat.id)
