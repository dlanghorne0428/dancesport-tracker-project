from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from cloudinary.models import CloudinaryField

def comp_logo_path(instance, filename):
    return "comps/{0}/{1}".format(instance.title, filename)

class Comp(models.Model):
    title = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()

    logo = CloudinaryField('logo', blank=True)

    # the different file formats pointed to by the URLs
    COMP_MNGR = 'CM'
    COMP_ORG = 'CO'
    NDCA_PREM = 'ND'
    O2CM = "O2"
    DATA_FORMAT_CHOICES = [
        (COMP_MNGR, 'Comp Manager'),
        (COMP_ORG, 'Comp Organizer'),
        (NDCA_PREM , 'NDCA Premier'),
        (O2CM, 'O2cm.com')
    ]
    url_data_format = models.CharField(
        max_length=2,
        choices=DATA_FORMAT_CHOICES,
        default=COMP_MNGR,
        )

    # URLs are optional, blank=True allows that, use heatlist_file if URL not available
    heatsheet_url = models.URLField(blank=True)
    #heatsheet_file = models.ImageField(upload_to=comp_logo_path, blank=True, storage=RawMediaCloudinaryStorage())
    heatsheet_file = models.FileField(upload_to=comp_logo_path, blank=True, storage=RawMediaCloudinaryStorage())
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
