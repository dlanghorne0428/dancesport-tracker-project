from django.db import models
from comps.models.heat import Heat
from rankings.models import Couple


class Heat_Entry(models.Model):
    ''' Store heat entry and result information for a single couple.'''
    couple = models.ForeignKey("rankings.Couple", on_delete=models.SET_NULL, null=True)
    heat = models.ForeignKey("Heat", on_delete=models.CASCADE, null=True)

    # store the shirt number of this couple in this heat. Used for looking up results.
    shirt_number = models.CharField(max_length=10, blank=True)

    # store the heatsheet code for which dancer?. Used for looking up results
    code = models.CharField(max_length=10, blank=True)

    # store the result placement, could be a digit 1 - 9, or a string indicating the prelim round
    result = models.CharField(max_length=10, blank=True)

    # store the point value earned by this couple in this heatsheet
    points = models.FloatField(null=True)


    def populate(self, heat_obj, couple_obj=None, scoresheet_code=None, shirt_number="???"):
        # a reference to the heat information
        self.heat = heat_obj
        if couple_obj is not None:
            self.couple = couple_obj

        # one member of the couple will have a shirt number
        # TODO: need to find couple
        #self.couple = dancer_name + " and " + partner_name
        self.shirt_number = shirt_number

        # the code is a string associated with the dancer, which can be used to
        # look up results from a scoresheet.
        if scoresheet_code is not None:
            self.code = scoresheet_code

        self.result = ""


    def __lt__(self, h):
        return self.heat < h.heat


    def __str__(self):
        return str(self.heat) + ": " + str(self.couple)
