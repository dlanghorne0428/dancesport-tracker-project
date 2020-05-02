# couple_matching.py
#
# this file contains various routines on finding matching couples based on partial names

from .models import Dancer, Couple
from comps.models import HeatlistDancer


def split_name(name):
    name_fields = name.split(",")
    if len(name_fields) == 2:
        # look for middle name
        first_fields = name_fields[1][1:].split()
        if len(first_fields) == 1:
            # no middle name
            return (name_fields[0], first_fields[0], "")
        else:
            # TODO: what if two middle names?
            return (name_fields[0], first_fields[0], first_fields[1])
    else:
        print("could not split name:", name)
        return(name, '', '')


def find_last_name_matches(dancers, dancer_1_code, dancer_2_code):
    partial_matches = list()
    for d in dancers:
        couples = Couple.objects.filter(dancer_1 = d)
        for c in couples:
            partial_matches.append((c, dancer_1_code))
        couples = Couple.objects.filter(dancer_2 = d)
        for c in couples:
            partial_matches.append((c, dancer_2_code))
    return partial_matches


def find_couple_partial_match(dancer, partner):
    dancer_last, dancer_first, dancer_middle = split_name(dancer.name)
    partner_last, partner_first, partner_middle = split_name(partner.name)
    partial_matching_couples = list()

    dancers = Dancer.objects.filter(name_last = dancer_last)
    partial_matches = find_last_name_matches(dancers, dancer.code, partner.code)
    for p in partial_matches:
        if p not in partial_matching_couples:
            partial_matching_couples.append(p)

    if partner_last != dancer_last:
        partners = Dancer.objects.filter(name_last = partner_last)
        partial_matches = find_last_name_matches(partners, partner.code, dancer.code)
        for p in partial_matches:
            if p not in partial_matching_couples:
                partial_matching_couples.append(p)

    return partial_matching_couples


def find_couple_exact_match(heatlist_dancer, heatlist_partner, couple_type):
    dancer_last, dancer_first, dancer_middle = split_name(heatlist_dancer.name)
    partner_last, partner_first, partner_middle = split_name(heatlist_partner.name)
    try:
        dancer = Dancer.objects.get(name_last = dancer_last, name_first = dancer_first, name_middle = dancer_middle)
    except:
        return (None, None)
    try:
        partner = Dancer.objects.get(name_last = partner_last, name_first = partner_first, name_middle = partner_middle)
    except:
        return (None, None)

    couples = Couple.objects.filter(dancer_1 = dancer, dancer_2 = partner, couple_type = couple_type)
    matches = couples.count()
    if matches > 1:
        print("Error: multiple matches for", heatlist_dancer.name, "and", heatlist_partner.name)
        print(matches)
        return (None, None)
    elif matches == 1:
        return (couples.first(), heatlist_dancer.code)
    else:
        couples = Couple.objects.filter(dancer_2 = dancer, dancer_1 = partner, couple_type = couple_type)
        matches = couples.count()
        if matches > 1:
            print("Error: multiple matches for", heatlist_dancer.name, "and", heatlist_partner.name)
            print(matches)
            return (None, None)
        elif matches == 1:
            return (couples.first(), heatlist_partner.code)
        else:
            return (None, None)
