from django.db import models
from comps.models.comp import Comp
from rankings.models.couple import Couple


class Comp_Couple(models.Model):
    ''' Store shirt number for a couple at a specific comp.'''
    couple = models.ForeignKey("rankings.Couple", on_delete=models.SET_NULL, null=True)
    comp = models.ForeignKey("Comp", on_delete=models.CASCADE, null=True)

    # store the shirt number of this couple at this comp
    shirt_number = models.CharField(max_length=10, blank=True)


    def populate(self, comp_obj, couple_obj, shirt_number):
        self.comp = comp_obj
        self.couple = couple_obj
        self.shirt_number = shirt_number


    def __lt__(self, cc):
        if self.comp == cc.comp:
            if self.shirt_number == cc.shirt_number:
                return self.couple < cc.couple
            else:
                return self.shirt_number < cc.shirt_number
        else:
            return self.comp < cc.comp


    def __str__(self):
        return str(self.comp) + ": " + str(self.couple) + " #" + self.shirt_number
