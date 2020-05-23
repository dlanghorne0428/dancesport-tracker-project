from django.db import models
from comps.models.heatlist_dancer import Heatlist_Dancer


class Unmatched_Heat_Entry(models.Model):
    '''Hold information about a possible matching couple for a HeatEntry.'''

    # identify a heat entry
    entry = models.ForeignKey('Heat_Entry', on_delete = models.CASCADE)

    # identify the Dancer and Partner as specified by the heatsheet
    dancer = models.ForeignKey('Heatlist_Dancer', on_delete = models.CASCADE, related_name="dancer_1")
    partner = models.ForeignKey('Heatlist_Dancer', on_delete = models.CASCADE, related_name="dancer_2")


    def populate(self, heat_entry_obj, heatlist_dancer, heatlist_partner):
        # a reference to the heat information
        self.entry = heat_entry_obj
        self.dancer = heatlist_dancer
        self.partner = heatlist_partner


    def __str__(self):
        return str(self.entry) + "Names: "+ str(self.dancer) + " and  " + str(self.partner)
