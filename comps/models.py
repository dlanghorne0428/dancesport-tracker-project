import time
from datetime import date, datetime, timezone, timedelta
from django.db import models
from rankings.models import Couple
from .scoresheet.calc_points import pro_heat_level, non_pro_heat_level

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

    # URLs are optional, blank=True allows that, use heatlist_file if URL not available
    heatsheet_url = models.URLField(blank=True)
    heatsheet_file = models.FileField(upload_to=comp_logo_path, blank=True)
    scoresheet_url = models.URLField(blank=True)

    # the different states of processing a competition
    INITIAL = "IN"
    DANCERS_LOADED = "DL"
    DANCER_NAMES_FORMATTED = "DNF"
    HEATS_LOADED = "HL"
    HEAT_STYLES_DEFINED = "HSD"
    HEAT_LEVELS_DEFINED = "HLD"
    HEAT_ENTRIES_MATCHED = "CEM"
    SCORESHEETS_LOADED = "SSL"
    RESULTS_RESOLVED = "RR"
    COMPLETE = "FIN"
    PROCESS_STATE_CHOICES = [
        (INITIAL, 'Comp Initialized'),
        (DANCERS_LOADED, 'Dancers Loaded'),
        (DANCER_NAMES_FORMATTED, 'Dancer Names Formatted'),
        (HEATS_LOADED, 'Heats Loaded'),
        (HEAT_STYLES_DEFINED, 'Heat Styles Defined'),
        (HEAT_LEVELS_DEFINED, 'Heat Levels Defined'),
        (HEAT_ENTRIES_MATCHED, 'Heat Entries Matched'),
        (SCORESHEETS_LOADED, 'Scoresheets Loaded'),
        (RESULTS_RESOLVED, 'Results Resolved '),
        (COMPLETE, 'Processing Complete')
    ]

    process_state = models.CharField(
        max_length = 3,
        choices=PROCESS_STATE_CHOICES,
        default=INITIAL,
        )

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
        (CABARET, "Cabaret-Theater_Arts"),
        (NIGHTCLUB, "Nightclub"),
        (COUNTRY, "Country_Western"),
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
        if "AC-" in s or "AA-" in s or "Amateur" in s or "YY-" in s or "AM/AM" in s or "AmAm" in s:
            return True
        else:
            return False


    def junior_heat(self):
        '''This function returns True if the description indicates a junior or youth heat.'''
        s = self.info
        if "-Y" in s or "YY" in s or "Youth" in s or "YH" in s or "-LY" in s or "YU" in s or "YT" in s or \
           "-J" in s or "JR" in s or "J1" in s or "J2" in s or "Junior" in s or "JU" in s or "JNR" in s or\
           "PT" in s or "Preteen" in s or "P1" in s or "P2" in s or "Pre-Teen" in s or "Pre Teen" in s or \
           "High School" in s or "Elementary School" in s or \
           "-TB" in s or "Teddy Bear" in s or "TB" in s:

           # Under 21 heats are sometimes listed as youth, but should not be treated as juniors
           if "U21" in s or "Under 21" in s:
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
        return self.comp.title + " " + self.get_category_display() + " " + str(self.heat_number)


class HeatEntry(models.Model):
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

    # def __eq__(self, h):
    #     return self.heat == h.heat and self.couple == h.couple


class HeatlistDancer(models.Model):
    '''Define minimal info about a dancer read in from a heatlist.'''

    # the name field is in last, first middle format
    name = models.CharField(max_length=100, blank=True)

    # the code field is used to obtain scoresheet results for this dancer
    code = models.CharField(max_length = 20)

    # flag to indicate if the name needs additional formatting by the user
    formatting_needed = models.BooleanField(default=False)

    def format_name(self, orig_name, simple=True, split_on=1):
        '''This method converts a name into last, first format.
           If simple is true, the method will not attempt to format names with three or more fields.
           If simple is false, the split_on field will determine where to put the comma'''

        fields = orig_name.split()
        if simple:
            if len(fields) == 2:
                return fields[1] + ', '  + fields[0]
            else:
                print("format needed:", orig_name)
                self.formatting_needed = True
                return None
        else:
            name = ""
            for f in range(split_on, len(fields)):
                if f > split_on:
                    name += " "
                name += fields[f]
            name += ","
            for f in range(0, split_on):
                name += " " + fields[f]
            return name


    def load_from_comp_mngr(self, line):
        '''This method populates the object from a line of text from a CompMngr heatlist.'''
        # get the name
        start_pos = 8
        end_pos = line.find("</td>")
        self.name = line[start_pos:end_pos]
        # find the code
        start_pos = line.find("TABLE_CODE_") + len("TABLE_CODE_")
        end_pos = line.find("'", start_pos)
        self.code = line[start_pos:end_pos]


    def load_from_comp_org(self, line):
        '''This method populates the object from a line of text from a heatlist in CompOrganizer format.'''
        # find the ID code for this dancer
        start_pos = line.find('"id":"') + len('"id":"')
        end_pos = line.find('"', start_pos)
        self.code = line[start_pos:end_pos]

        if self.code != "0":
            # find the dancer's name
            start_pos = line.find('"name":"') + len('"name":"')
            end_pos = line.find('"', start_pos)
            orig_name = line[start_pos:end_pos]
            new_name = self.format_name(orig_name)
            if new_name is None:
                self.name = orig_name
            else:
                self.name = new_name
        else:
            print("Error - invalid code")


    def load_from_ndca_premier(self, line):
        '''This method populates the object from a line of text from a heatlist in NDCA Premier format.'''
        # find the dancer's name
        fields = line.split(">")
        orig_name = fields[1]
        new_name = self.format_name(orig_name)
        if new_name is None:
            self.name = orig_name
        else:
            self.name = new_name

        # find the ID code for this dancer
        pos = fields[0].find("competitor=") + len("competitor=")
        self.code = fields[0][pos+1:-1]


    def load_from_file(self, line):
        '''This method populates the object from a line of text from a heatlist in custom file format.'''
        # find the dancer's name
        fields = line.split(":")
        self.name = fields[0]
        self.code = fields[1]


    def __str__(self):
        return self.name


class UnmatchedHeatEntry(models.Model):
    '''Hold information about a possible matching couple for a HeatEntry.'''

    # identify a heat entry
    entry = models.ForeignKey('HeatEntry', on_delete = models.CASCADE)

    # identify the Dancer and Partner as specified by the heatsheet
    dancer = models.ForeignKey('HeatlistDancer', on_delete = models.CASCADE, related_name="dancer_1")
    partner = models.ForeignKey('HeatlistDancer', on_delete = models.CASCADE, related_name="dancer_2")

    # identify the potential couple, as stored in the heats_in_database
    #couple = models.ForeignKey('rankings.Couple', on_delete = models.CASCADE)

    # identify which scoresheet code to use if this couple ends up being matched
    #code = models.CharField(max_length = 20, blank=True, default='')

    def populate(self, heat_entry_obj, heatlist_dancer, heatlist_partner):
        # a reference to the heat information
        self.entry = heat_entry_obj
        self.dancer = heatlist_dancer
        self.partner = heatlist_partner


    def __str__(self):
        return str(self.entry) + "Names: "+ str(self.dancer) + " and  " + str(self.partner)
