import time
from datetime import date, datetime, timezone, timedelta
from django.db import models
from comps.models.comp import Comp
from rankings.models import Couple
from comps.scoresheet.calc_points import pro_heat_level, non_pro_heat_level


class Heat(models.Model):
    '''Define information for a single heat'''
    # refer to the competition that hosted this heat
    comp = models.ForeignKey('Comp', on_delete=models.CASCADE)

    # the category is either "Heat" or "Pro heat".
    # Each category has a separate sequence of heat numbers
    PRO_HEAT = 'PH'
    NORMAL_HEAT = 'NH'
    SOLO = "SO"
    CATEGORY_CHOICES = [
        (PRO_HEAT, "Pro heat"),
        (NORMAL_HEAT, "Heat"),
        (SOLO, "Solo"),
    ]
    category = models.CharField(max_length = 2, choices = CATEGORY_CHOICES, default = NORMAL_HEAT)
    heat_number = models.IntegerField()

    # the extra field is a string with additional info about the heat number
    # this can indicate a ballroom, or simply be a letter like A
    extra = models.CharField(max_length=20, blank=True)

    # the info field stores the description of the heat. It is used to
    # determine the level and dance style.
    info = models.CharField(max_length=200)

    # the different styles of ballroom dancing. couples are ranked in each style.
    SMOOTH = "SMOO"
    RHYTHM = "RHY"
    STANDARD = "STD"
    LATIN = "LAT"
    CABARET = "CAB" # also includes theater arts and showcases
    NIGHTCLUB = "NC"
    COUNTRY = "CTRY"
    COMBINED = "MIX" # for 9-dance, 10-dance events
    UNKNOWN = "UNK"
    DANCE_STYLE_CHOICES = [
        (SMOOTH, "Smooth"),
        (RHYTHM, "Rhythm"),
        (STANDARD,  "Standard"),
        (LATIN, "Latin"),
        (CABARET, "Cabaret-Theater_Arts"),
        (NIGHTCLUB, "Nightclub"),
        (COUNTRY, "Country_Western"),
        (COMBINED, "Combined"),
        (UNKNOWN, "Unknown"),
    ]
    style = models.CharField(max_length = 4, choices = DANCE_STYLE_CHOICES, default="UNK")

    # this field indicates the when the heat is scheduled to be danced
    time = models.DateTimeField(blank=True)

    # this field indicates if the heat had prelim rounds before the Final.
    rounds = models.CharField(max_length=20, default="F")  # default is Final only

    # this field stores the base point value for the winner of a final round only heat
    # value increases if preliminary rounds are danced
    base_value = models.IntegerField(blank=True)


    def set_level(self):
        if self.category == "PH":
            self.base_value = pro_heat_level(self.info)
        else:
            self.base_value = non_pro_heat_level(self.info, self.multi_dance())

    def remove_info_prefix(self):
        if self.info.startswith("L-"):
            self.info = self.info[2:]
        elif self.info.startswith("G-"):
            self.info = self.info[2:]
        elif self.info.startswith("AP-"):
            self.info = self.info[3:]
        elif self.info.startswith("PA-"):
            self.info = self.info[3:]

    # temporary
    def info_prefix(self):
        if self.info.startswith("L-"):
            return self.info[2:]
        elif self.info.startswith("G-"):
            return self.info[2:]
        elif self.info.startswith("AP-"):
            return self.info[3:]
        elif self.info.startswith("PA-"):
            return self.info[3:]
        else:
            return self.info


    def multi_dance(self):
        '''This function returns True if the description indicates a multi-dance heat.'''
        s = self.info
        left_pos = s.find('(')
        right_pos = s.find(')')
        if left_pos == -1 or right_pos == -1:
            return False
        elif "Mixed" in s or "ML" in s or "Solo Star" in s or "NP" in s:
            return False
        elif "/" in s[left_pos:right_pos] or "," in s[left_pos:right_pos]:
            return True
        else:
            return False


    def set_dance_style(self):
        '''This function determines the dance style based on the heat description.'''
        s = self.info
        if "Smooth" in s:
            self.style = Heat.SMOOTH
        elif "Rhythm" in s:
            self.style = Heat.RHYTHM
        elif "Latin" in s:
            self.style = Heat.LATIN
        elif "Standard" in s or "Ballroom" in s or "Balroom" in s or "Ballrom" in s:
            self.style = Heat.STANDARD
        elif "Nightclub" in s or "Night Club" in s or "NightClub" in s or "Niteclub" in s or "Nite Club" in s or "Caribbean" in s or "Club Dance" in s:
            self.style = Heat.NIGHTCLUB
        elif "Country" in s:
            self.style = Heat.COUNTRY
        elif "Cabaret" in s or "Theatre" in s or "Theater" in s or "Exhibition" in s:
            self.style = Heat.CABARET
        else:
            #TODO: ask user?
            if self.multi_dance():
                print("Unknown style for heat", s)
            self.style = Heat.UNKNOWN


    def set_time(self, time_str, day_of_week_str):
        comp_start_date = self.comp.start_date.isocalendar()
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        try:
            isoweekday = days_of_week.index(day_of_week_str) + 1
            heat_date = date.fromisocalendar(comp_start_date[0], comp_start_date[1], isoweekday)
        except:
            print(str(self), "Warning in day of week:", day_of_week_str)
            heat_date = self.comp.start_date
        try:
            time_of_day = time.strptime(time_str, "%I:%M%p")
        except:
            print(str(self), "Warning in time of day:", time_str)
            time_of_day = time.strptime("0:0", "%H:%M")
        tz = timezone(offset=timedelta(hours=0))  # avoid warnings about naive time, treat all times as UTC
                                                 # could try to get smarter about where comp was located, but why?
        self.time = datetime(heat_date.year, heat_date.month, heat_date.day,
                             time_of_day.tm_hour, time_of_day.tm_min, tzinfo=tz)


    def amateur_heat(self):
        '''This function returns True if the description indicates an amateur heat.'''
        if "Amateur" in self.comp.title:
            return True
        s = self.info
        if "AC-" in s or "AA-" in s or "Amateur" in s or "YY-" in s or "AM/AM" in s or "AmAm" in s or "Fordney" in s or "MLA" in s:
            return True
        else:
            return False


    def junior_heat(self):
        '''This function returns True if the description indicates a junior or youth heat.'''
        s = self.info
        s_upper = s.upper()
        if "-Y" in s or "YY" in s or "Youth" in s or "YH" in s_upper or "-LY" in s or "YU" in s or "YT" in s or s.startswith("Y") or\
           "-J" in s or "JR" in s or "J1" in s or "J2" in s or "Junior" in s or "JU" in s or "JNR" in s or\
           "PT" in s or "Preteen" in s or "P1" in s or "P2" in s or "Pre-Teen" in s or "Pre Teen" in s or \
           "High School" in s or "Elementary School" in s or \
           "-TB" in s or "Teddy Bear" in s or " TB" in s or "TB " in s:

           # Under 21 heats are sometimes listed as youth, but should not be treated as juniors
           if "U21" in s or "Under 21" in s or "Under-21" in s:
                return False
           else:
               return True
        else:
            return False


    def couple_type(self):
        if self.category == "Pro heat" or self.category == "PH": #Heat.PRO_HEAT:
            return Couple.PRO_COUPLE
        elif self.amateur_heat():
            if self.junior_heat():
                return Couple.JR_AMATEUR_COUPLE
            else:
                return Couple.AMATEUR_COUPLE
        else:
            if self.junior_heat():
                return Couple.JR_PRO_AM_COUPLE
            else:
                return Couple.PRO_AM_COUPLE


    def __lt__(self, h):
        ''' override < operator to sort heats by various fields.'''
        # if times are the same, sort by number
        if self.time == h.time:
            return self.heat_number < h.heat_number
        else: # use the time to determine order
            return self.time < h.time


    def __str__(self):
        return self.comp.title + " " + self.get_category_display() + " " + str(self.heat_number)
