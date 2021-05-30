from django.db import models
from comps.models.comp import Comp
from comps.models.heat import Heat
from comps.models.heatlist_dancer import Heatlist_Dancer

class Heatlist_Error(models.Model):
    '''Define info about an anomaly found when processing a heatlist.'''

    # the comp where this error was encountered
    comp = models.ForeignKey("comps.Comp", on_delete=models.CASCADE)

    # the heat where this error was encountered
    heat = models.ForeignKey("comps.Heat", on_delete=models.CASCADE, null=True)

    # the dancer's name whose heats were being processed when the error was encountered
    dancer = models.CharField(max_length=100, blank=True)

    # the different errors that may be encountered
    NO_ERROR = "NO_ERR"
    UNKNOWN_LEVEL = "UNK_LEV"
    UNKNOWN_STYLE = "UNK_STYL"
    NO_HEAT_COUNT = "NO_COUNT"
    NO_CODE_FOUND = "NO_CODE"
    NO_PARTNER_FOUND = "NO_PRTNR"
    PARSING_ERROR = "PARS_ERR"
    HEAT_TIME_INVALID = "BAD_TIME"
    ERROR_CHOICES = [
        (NO_ERROR , 'No Error'),
        (UNKNOWN_LEVEL, 'Unknown Event Level'),
        (UNKNOWN_STYLE, 'Unknown Event Style'),
        (NO_HEAT_COUNT, 'Heat Count Not Found'),
        (NO_HEAT_COUNT, 'Scoresheet Code Not Found'),
        (NO_PARTNER_FOUND, 'Partner Not Found'),
        (PARSING_ERROR, 'Unable to Parse Heat'),
        (HEAT_TIME_INVALID, 'Invalid Heat Time')
    ]

    error = models.CharField(
        max_length = 8,
        choices=ERROR_CHOICES,
        default="NO_ERR",
        )
