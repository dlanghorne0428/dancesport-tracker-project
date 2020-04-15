from django.db import models
from rankings.models import Couple

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


    class HeatResult(models.Model):
        ''' Store result information for a single couple.'''
        couple: models.ForeignKey("Couple", on_delete=models.SET_NULL, null=True)
        heat: models.ForeignKey("Heat", on_delete=models.CASCADE)

        # store the shirt number of this couple in this heat. Used for looking up results.
        shirt_number = models.CharField(max_length=10, blank=True)

        # store the heatsheet code for which dancer?. Used for looking up results
        code = models.CharField(max_length=10, blank=True)

        # store the result placement, could be a digit 1 - 9, or a string indicating the prelim round
        result = models.CharField(max_length=10, blank=True)

        # store the point value earned by this couple in this heatsheet
        points = models.FloatField(blank=True)
