import json
from operator import itemgetter

from .models import Heat
from rankings.models import Couple, Dancer

age_div_prefix_list = ("L-", "G-", "AC-", "Pro ", "AC-", "Professional", "AM/AM", "Amateur", "Youth", "MF-", "M/F")

class Heatlist():
    '''This class is a base class to store heat list information for a competition.'''

    def __init__(self):
        # store the name of the comp,
        self.comp_name = "--Click Open to load a Heat Sheet File--"
        self.dancers = list()               # store a list of the individual dancers competing
        self.couples = list()               # store a list of the couples competing
        self.heats = list()
        self.heat_entries = list()


    ############### DANCER / COUPLE ROUTINES  ###########################################
    # the following methods deal with dancers and couples in the competition
    #####################################################################################
    def dancer_name_list(self):
        '''This method returns a list of dancer names in this competition.'''
        l = list()
        for d in self.dancers:
            l.append(d.name)
        return l
