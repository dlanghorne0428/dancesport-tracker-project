from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.models.unmatched_heat_entry import Unmatched_Heat_Entry
from comps.models.heatlist_dancer import Heatlist_Dancer
from rankings.models import Dancer, Couple
from rankings.couple_matching import find_couple_partial_match, find_couple_first_letter_match, find_dancer_exact_match, resolve_unmatched_entries

def save_alias(unmatched_dancer, actual_dancer):
    if unmatched_dancer.alias is None:
        if unmatched_dancer.alias != str(actual_dancer):
            unmatched_dancer.alias = actual_dancer
            unmatched_dancer.save()
            print("Alias for " + unmatched_dancer.name + " is " + str(actual_dancer))
        else:
            print("No alias needed for " + unmatched_dancer.name + " matches " + str(actual_dancer))
    else:
        print("Alias for " + unmatched_dancer.name + " already assigned as " + str(unmatched_dancer.alias))


def resolve_mismatches(request, comp_id, wider_search=0):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    unmatched_entries = Unmatched_Heat_Entry.objects.all().order_by('entry')
    comp = get_object_or_404(Comp, pk=comp_id)
    if unmatched_entries.count() == 0:
        # all unmatched entries resolved, delete heatlist_dancer entries from database
        # don't do this here, we want to save the aliases discovered and delete later
        # heatlist_dancers = Heatlist_Dancer.objects.all().delete()
        if comp.process_state == comp.SCORESHEETS_LOADED:
            comp.process_state = comp.RESULTS_RESOLVED
        else:
            comp.process_state = comp.HEAT_ENTRIES_MATCHED
        comp.save()
        return redirect("comps:comp_heats", comp_id)
    else:
        first_unmatched = unmatched_entries.first()
        similar_unmatched = Unmatched_Heat_Entry.objects.filter(dancer=first_unmatched.dancer, partner=first_unmatched.partner)
        dancer_match = find_dancer_exact_match(first_unmatched.dancer)
        partner_match = find_dancer_exact_match(first_unmatched.partner)
        if wider_search == 0:
            possible_matches = find_couple_partial_match(first_unmatched.dancer, first_unmatched.partner)
        elif wider_search == 1:
            possible_matches = find_couple_first_letter_match(first_unmatched.dancer, first_unmatched.partner)
        else:
            possible_matches = find_couple_first_letter_match(first_unmatched.dancer, first_unmatched.partner, dancer_only=False)

        if request.method == "GET":
            possible_couples = list()
            for i in range(len(possible_matches)):
                possible_couples.append(possible_matches[i][0])
            possible_couples.sort()
            return render(request, "comps/resolve_mismatches.html", {'comp':comp, 'first_entry': first_unmatched,
                                                                     'dancer_match': dancer_match, 'partner_match': partner_match,
                                                                     'possible_matches': possible_couples,
                                                                     'couple_type': first_unmatched.entry.heat.couple_type(),
                                                                     'entries_remaining': unmatched_entries.count()})
        else: # POST
            submit = request.POST.get("submit")
            if submit.startswith("Dancer"):
                name_str = submit[len("Dancer: "):]
                return redirect('create_dancer', name_str, comp_id)

            elif submit.startswith("Couple"):
                couple_type = first_unmatched.entry.heat.couple_type()
                start_pos = len("Couple: ")
                end_pos = submit.find(" and ")
                name_str = submit[start_pos:end_pos]
                #print("Name: " + name_str + " match: " + first_unmatched.dancer.name,"**")
                if name_str == first_unmatched.dancer.name:
                    dancer_id = dancer_match.id
                    partner_id = partner_match.id
                    code = first_unmatched.dancer.code
                else:
                    dancer_id = partner_match.id
                    partner_id = dancer_match.id
                    code = first_unmatched.partner.code

                new_couple = Couple()
                dancer_1 = Dancer.objects.get(pk=dancer_id)
                dancer_2 = Dancer.objects.get(pk=partner_id)
                new_couple.dancer_1 = dancer_1
                new_couple.dancer_2 = dancer_2
                new_couple.couple_type = couple_type
                try:
                    new_couple.save()
                    resolve_unmatched_entries(new_couple, code, similar_unmatched)
                except:
                    new_couple.delete()

                return redirect('comps:resolve_mismatches', comp_id = comp_id)

            elif submit == "Widen Search":
                if wider_search < 2:
                    wider_search += 1
                return redirect('comps:resolve_mismatches', comp_id = comp_id, wider_search=wider_search)

            elif submit == "Select" or submit == "Override Type":
                couple_str = request.POST.get("couple")
                for pm_couple, pm_code in possible_matches:
                    if str(pm_couple) == couple_str and (pm_couple.couple_type == first_unmatched.entry.heat.couple_type() or submit == "Override Type"):
                        print(couple_str, first_unmatched.dancer.name, first_unmatched.partner.name)
                        # assign aliases
                        if first_unmatched.dancer.name in couple_str:
                            if first_unmatched.dancer.name == str(pm_couple.dancer_1):
                                save_alias(first_unmatched.partner, pm_couple.dancer_2)
                                resolve_unmatched_entries(pm_couple, pm_code, similar_unmatched, submit == "Override Type")
                            else:
                                save_alias(first_unmatched.partner, pm_couple.dancer_1)
                                resolve_unmatched_entries(pm_couple, pm_code, similar_unmatched, submit == "Override Type")

                        elif first_unmatched.partner.name in couple_str:
                            if first_unmatched.partner.name == str(pm_couple.dancer_1):
                                save_alias(first_unmatched.dancer, pm_couple.dancer_2)
                                # if first_unmatched.dancer.alias is None:
                                #     first_unmatched.dancer.alias = pm_couple.dancer_2
                                #     first_unmatched.dancer.save()
                                #     print("Alias for " + first_unmatched.dancer.name + " is " + str(pm_couple.dancer_2))
                                # else:
                                #     print("Alias for " + first_unmatched.dancer.name + " already assigned as " + str(first_unmatched.dancer.alias))
                                resolve_unmatched_entries(pm_couple, pm_code, similar_unmatched, submit == "Override Type")
                            else:
                                save_alias(first_unmatched.dancer, pm_couple.dancer_1)
                                # if first_unmatched.dancer.alias is None:
                                #     first_unmatched.dancer.alias = pm_couple.dancer_1
                                #     first_unmatched.dancer.save()
                                #     print("Alias for " + first_unmatched.dancer.name + " is " + str(pm_couple.dancer_1))
                                # else:
                                #     print("Alias for " + first_unmatched.dancer.name + " already assigned as " + str(first_unmatched.dancer.alias))
                                resolve_unmatched_entries(pm_couple, pm_code, similar_unmatched, submit == "Override Type")

                        else:
                            print("Need alias for both")
                        #resolve_unmatched_entries(pm_couple, pm_code, similar_unmatched, submit == "Override Type")
                        break
                return redirect('comps:resolve_mismatches', comp_id = comp_id)
            elif submit == "Delete":
                # deleting the heat entry that this unmatched entry points to will also delete all the unmatched entries
                # that point to the same entry.
                the_couple_type = first_unmatched.entry.heat.couple_type()
                #similar_unmatched = Unmatched_Heat_Entry.objects.filter(dancer=first_unmatched.dancer, partner=first_unmatched.partner)
                for e in similar_unmatched:
                    if the_couple_type == e.entry.heat.couple_type():
                        e.delete()
                return redirect("comps:heat", first_unmatched.entry.heat.id)
