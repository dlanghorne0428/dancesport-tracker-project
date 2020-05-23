
from rankings.models import Couple, Dancer
from rankings.couple_matching import find_couple_exact_match
from comps.models.heat import Heat
from comps.models.heat_entry import Heat_Entry
from comps.models.unmatched_heat_entry import Unmatched_Heat_Entry


age_div_prefix_list = ("L-", "G-", "AC-", "Pro ", "AC-", "Professional", "AM/AM", "Amateur", "Youth", "MF-", "M/F")

class Heatlist():
    '''This class is a base class to store heat list information for a competition.'''

    def __init__(self):
        # store the name of the comp,
        self.comp_name = "--Click Open to load a Heat Sheet File--"
        self.unmatched_entries = 0
        self.dancers = list()               # store a list of the individual dancers competing


    ############### DANCER / COUPLE ROUTINES  ###########################################
    # the following methods deal with dancers and couples in the competition
    #####################################################################################
    def dancer_name_list(self):
        '''This method returns a list of dancer names in this competition.'''
        l = list()
        for d in self.dancers:
            l.append(d.name)
        return l

    def find_dancer(self, dancer_name, format_needed = False):
        '''This method finds the dancer object from the list based on the name.'''
        for d in self.dancers:
            if format_needed:
                name_fields = dancer_name.split()
                for f in range(1, len(name_fields)):
                    name_scramble = d.format_name(dancer_name, simple=False, split_on=f)
                    if d.name == name_scramble:
                        return d
            else:
                if d.name == dancer_name:
                    return d
        else:
            return None


    def add_heat_to_database(self, heat, comp_ref):
        if heat.category == Heat.PRO_HEAT or heat.multi_dance():
            heats_in_database = Heat.objects.filter(comp=comp_ref, category=heat.category, heat_number=heat.heat_number, info=heat.info)
            if heats_in_database.count() > 0:
                h = heats_in_database.first()
            else:
                h = heat
                print(h)
                h.save()   # save the heat into the database
            return h
        else: # not a heat that we care about
            return None


    def build_heat_entry(self, heat, dancer, partner, shirt_number):
        '''This method builds a HeatEntry object for the current dancer, partner, and shirt number.'''

        couple_type = heat.couple_type()
        couple, code = find_couple_exact_match(dancer, partner, couple_type)
        heat_entry_obj = Heat_Entry()
        # populate and save matching heat entry
        if couple is not None:
            heat_entry_obj.populate(heat, couple, code, shirt_number)
            entries_in_database = Heat_Entry.objects.filter(heat=heat, couple=couple, shirt_number=shirt_number)
            if entries_in_database.count() == 0:
                heat_entry_obj.save()
        else:
            # populate and save partially completed heat entry
            heat_entry_obj.populate(heat, shirt_number=shirt_number)
            entries_in_database = Heat_Entry.objects.filter(heat=heat, shirt_number=shirt_number)
            if entries_in_database.count() == 0:
                heat_entry_obj.save()
                he = heat_entry_obj
            else:
                he = entries_in_database.first()

            # save this unmatched heat entry, unless it's already there for some reason
            mismatches_in_database = Unmatched_Heat_Entry.objects.filter(entry=he, dancer=dancer, partner=partner)
            if mismatches_in_database.count() == 0:
                mismatch = Unmatched_Heat_Entry()
                mismatch.populate(he, dancer, partner)
                mismatch.save()

            self.unmatched_entries += 1
