from django.db import models
from comps.models.comp import Comp
from comps.models.heat import Heat
from rankings.models import Couple

class Result_Error(models.Model):
    '''Define info about an anomaly found when processing a scoresheet.'''

    # the comp where this error was encountered
    comp = models.ForeignKey("comps.Comp", on_delete=models.CASCADE, null=True)

    # the heat where this error was encountered
    heat = models.ForeignKey("comps.Heat", on_delete=models.CASCADE, null=True)

    # the couple whose results were being processed when the error was encountered
    couple = models.ForeignKey("rankings.Couple", on_delete=models.SET_NULL, null=True)

    # the different errors that may be encountered
    NO_ERROR = "NO_ERR"
    UNKNOWN_LEVEL = "UNK_LEV"
    UNKNOWN_STYLE = "UNK_STYL"
    HEAT_NOT_FOUND = "NO_SCORE"
    NO_ENTRIES_FOUND = "NO_ENT"
    NO_RESULTS_FOUND = "NO_RES"
    NO_COUPLE_RESULT = "NO_COUPL"
    TWO_RESULTS_FOR_COUPLE = "TWO_RES"
    UNEXPECTED_EARLY_ROUND = "EARLY_RD"
    LATE_ENTRY = "LATE_ENT"
    ERROR_CHOICES = [
        (NO_ERROR , 'No Error'),
        (UNKNOWN_LEVEL, 'Unknown Event Level'),
        (UNKNOWN_STYLE, 'Unknown Event Style'),
        (HEAT_NOT_FOUND, 'Heat Info Not Found'),
        (NO_ENTRIES_FOUND, 'No Entries in Heat'),
        (NO_RESULTS_FOUND, 'No Results Found for Heat'),
        (NO_COUPLE_RESULT, 'No Results Found for Couple'),
        (TWO_RESULTS_FOR_COUPLE, 'Two Results Found for Couple'),
        (UNEXPECTED_EARLY_ROUND, 'Unexpected Early Round'),
        (LATE_ENTRY, 'Late Entry')
    ]

    error = models.CharField(
        max_length = 8,
        choices=ERROR_CHOICES,
        default="NO_ERR",
        )
