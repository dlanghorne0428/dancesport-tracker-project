from django.shortcuts import render, redirect, get_object_or_404
from comps.models.comp import Comp
from comps.models.comp_couple import Comp_Couple
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.models.unmatched_heat_entry import Unmatched_Heat_Entry
from comps.models.heatlist_dancer import Heatlist_Dancer
from rankings.models import Dancer, Couple
from rankings.couple_matching import find_couple_partial_match, find_couple_first_letter_match, find_dancer_exact_match, resolve_unmatched_entries


def save_alias(unmatched_dancer, actual_dancer):
    # if the unmatched dancer doesn't have an alias and the actual dancer's name is spelled differently,
    # update the unmatched dancer to remember the actual dancer as an alias.
    if unmatched_dancer.alias is None:
        if unmatched_dancer.name != str(actual_dancer):
            unmatched_dancer.alias = actual_dancer
            unmatched_dancer.save()


def resolve_mismatches(request, comp_id, wider_search=0):
    if not request.user.is_superuser:
        return render(request, 'rankings/permission_denied.html')
    unmatched_entries = Unmatched_Heat_Entry.objects.all().order_by('entry')
    comp = get_object_or_404(Comp, pk=comp_id)
    if unmatched_entries.count() == 0:
        # all unmatched entries resolved, delete heatlist_dancer entries without an alias from database
        heatlist_dancers = Heatlist_Dancer.objects.filter(comp=comp)
        orig_count = heatlist_dancers.count()
        for hld in heatlist_dancers:
            if hld.alias is None:
                hld.delete()
        new_count = Heatlist_Dancer.objects.filter(comp=comp).count()
        print("Aliases found: " + str(new_count) + ". Deleted " + str(orig_count - new_count) + " objects.")

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
                    comp_couple_obj = Comp_Couple()
                    comp_couple_obj.populate(comp, new_couple, first_unmatched.entry, shirt_number)
                    comp_couple_obj.save()
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
                        # don't assign aliases if this is a late entry
                        if first_unmatched.entry.code != "LATE":
                            # assign aliases, if one matches, the other must be an alias
                            if first_unmatched.dancer.name == str(pm_couple.dancer_1):
                                save_alias(first_unmatched.partner, pm_couple.dancer_2)
                            elif first_unmatched.dancer.name == str(pm_couple.dancer_2):
                                save_alias(first_unmatched.partner, pm_couple.dancer_1)
                            elif first_unmatched.partner.name == str(pm_couple.dancer_1):
                                save_alias(first_unmatched.dancer, pm_couple.dancer_2)
                            elif first_unmatched.partner.name == str(pm_couple.dancer_2):
                                save_alias(first_unmatched.dancer, pm_couple.dancer_1)

                            # neither names match, try to use first letter of last name

                            # both dancer and partner have same first letter of last name, don't try to assign alias
                            elif first_unmatched.dancer.name[0] == first_unmatched.partner.name[0]:
                                print("Need alias for " + first_unmatched.dancer.name + " and " + first_unmatched.partner.name + " Couple is " + str(pm_couple))

                            # last names start with different letters, use that to assign aliases to each member of the couple
                            elif first_unmatched.dancer.name[0] == pm_couple.dancer_1.name_last[0]:
                                save_alias(first_unmatched.dancer, pm_couple.dancer_1)
                                save_alias(first_unmatched.partner, pm_couple.dancer_2)
                            elif first_unmatched.partner.name[0] == pm_couple.dancer_1.name_last[0]:
                                save_alias(first_unmatched.partner, pm_couple.dancer_1)
                                save_alias(first_unmatched.dancer, pm_couple.dancer_2)
                            elif first_unmatched.dancer.name[0] == pm_couple.dancer_2.name_last[0]:
                                save_alias(first_unmatched.dancer, pm_couple.dancer_2)
                                save_alias(first_unmatched.partner, pm_couple.dancer_1)
                            elif first_unmatched.partner.name[0] == pm_couple.dancer_2.name_last[0]:
                                save_alias(first_unmatched.partner, pm_couple.dancer_2)
                                save_alias(first_unmatched.dancer, pm_couple.dancer_1)

                            else: # neither name matches the first letter of last name, don't try to assign aliases
                                print("Need alias for " + first_unmatched.dancer.name + " and " + first_unmatched.partner.name + " Couple is " + str(pm_couple))

                        # save resolved couple in comp_couple
                        comp_couple_obj = Comp_Couple()
                        comp_couple_obj.populate(comp, pm_couple, first_unmatched.entry.shirt_number)
                        comp_couple_obj.save()
                        resolve_unmatched_entries(pm_couple, pm_code, similar_unmatched, submit == "Override Type")
                        break
                return redirect('comps:resolve_mismatches', comp_id = comp_id)
            elif submit == "Delete":
                # deleting the heat entry that this unmatched entry points to will also delete all the unmatched entries
                # that point to the same entry.
                the_couple_type = first_unmatched.entry.heat.couple_type()
                #similar_unmatched = Unmatched_Heat_Entry.objects.filter(dancer=first_unmatched.dancer, partner=first_unmatched.partner)
                for e in similar_unmatched:
                    if the_couple_type == e.entry.heat.couple_type():
                        e.entry.delete()
                        e.delete()
                return redirect("comps:heat", first_unmatched.entry.heat.id)
