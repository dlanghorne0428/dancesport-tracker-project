import time
from datetime import date, datetime, timezone, timedelta
from django.db import models
from rankings.models import Couple
from .calc_points import pro_heat_level, non_pro_heat_level

def comp_logo_path(instance, filename):
    return "comps/{0}/{1}".format(instance.title, filename)

class Comp(models.Model):
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    logo = models.ImageField(upload_to=comp_logo_path, blank=True)

    # the different file formats pointed to by the URLs
    COMP_MNGR = 'CM'
    COMP_ORG = 'CO'
    NDCA_PREM = 'ND'
    DATA_FORMAT_CHOICES = [
        (COMP_MNGR, 'Comp Manager'),
        (COMP_ORG, 'Comp Organizer'),
        (NDCA_PREM , 'NDCA Premier'),
    ]
    url_data_format = models.CharField(
        max_length=2,
        choices=DATA_FORMAT_CHOICES,
        default=COMP_MNGR,
    )

    # URLs are optional, blank=True allows that
    heatsheet_url = models.URLField(blank=True)
    scoresheet_url = models.URLField(blank=True)

    def __str__(self):
        return self.title


class Heat(models.Model):
    '''Define information for a single heat'''
    # refer to the competition that hosted this heat
    comp = models.ForeignKey('Comp', on_delete=models.CASCADE)

    # the category is either "Heat" or "Pro heat".
    # Each category has a separate sequence of heat numbers
    PRO_HEAT = 'PH'
    NORMAL_HEAT = 'NH'
    CATEGORY_CHOICES = [
        (PRO_HEAT, "Pro heat"),
        (NORMAL_HEAT, "Heat"),
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
        (CABARET, "Cabaret / Theater Arts"),
        (NIGHTCLUB, "Night Club"),
        (COUNTRY, "Country Western"),
        (COMBINED, "Combined"),
        (UNKNOWN, "Unknown"),
    ]
    style = models.CharField(max_length = 4, choices = DANCE_STYLE_CHOICES, default="UNK")

    # these fields indicate the when the heat is scheduled to be danced
    session = models.CharField(max_length=20, blank=True)
    time = models.DateTimeField(blank=True)

    # this field indicates if the heat had prelim rounds before the Final.
    rounds = models.CharField(max_length=20, default="F")  # default is Final only

    # this fields stores the base point value for the winner of a final round only heat
    # value increases if preliminary rounds are danced
    base_value = models.IntegerField(blank=True)

    def set_level(self):
        if self.category == "PH":
            self.base_value = pro_heat_level(self.info)
        else:
            self.base_value = non_pro_heat_level(self.info, self.multi_dance())

    def multi_dance(self):
        '''This function returns True if the description indicates a multi-dance heat.'''
        s = self.info
        left_pos = s.find('(')
        right_pos = s.find(')')
        if left_pos == -1 or right_pos == -1:
            return False
        elif "Mixed" in s or "Solo Star" in s or "NP" in s:
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
        elif "Nightclub" in s or "Night Club" in s or "NightClub" in s or "Niteclub" in s or "Nite Club" in s or "Caribbean" in s:
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
        isoweekday = days_of_week.index(day_of_week_str) + 1
        heat_date = date.fromisocalendar(comp_start_date[0], comp_start_date[1], isoweekday)
        time_of_day = time.strptime(time_str, "%I:%M%p")
        tz = timezone(offset=timedelta(hours=0))  # avoid warnings about naive time, treat all times as UTC
                                                 # could try to get smarter about where comp was located, but why?
        self.time = datetime(heat_date.year, heat_date.month, heat_date.day,
                             time_of_day.tm_hour, time_of_day.tm_min, tzinfo=tz)

    def __lt__(self, h):
        ''' override < operator to sort heats by various fields.'''
        # if session numbers are the same, sort by time
        if self.session == h.session:
            return self.time < h.time
        else: # use the session numbers to determine order
            return self.session < h.session

    #
    # def __eq__(self, h):
    #     ''' override == operator to compare category and number'''
    #     return (self.category == h.category) and (self.heat_number == h.heat_number)

    def __str__(self):
        return self.comp.title + " " + self.category + " " + self.heat_number.__str__()


class HeatResult(models.Model):
    ''' Store result information for a single couple.'''
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

    def populate(self, heat_obj, couple_obj, scoresheet_code, shirt_number="???"):
        # a reference to the heat information
        self.heat = heat_obj
        self.couple = couple_obj

        # one member of the couple will have a shirt number
        # TODO: need to find couple
        #self.couple = dancer_name + " and " + partner_name
        self.shirt_number = shirt_number

        # the code is a string associated with the dancer, which can be used to
        # look up results from a scoresheet.
        # TODO: for which dancer?
        self.code = scoresheet_code

        self.result = ""


    def __lt__(self, h):
        return self.heat < h.heat

    # def __eq__(self, h):
    #     return self.heat == h.heat and self.couple == h.couple
