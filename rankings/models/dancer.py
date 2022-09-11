from django.db import models
from datetime import date

# dancer type has choices
PRO = 'PRO'
ADULT_AMATEUR = 'AM'
JUNIOR_AMATEUR = 'JR'
DANCER_TYPE_CHOICES = [
    (PRO, 'Professional'),
    (ADULT_AMATEUR, 'Amateur'),
    (JUNIOR_AMATEUR , 'Junior'),
]

class Dancer(models.Model):
    # name fields
    name_first = models.CharField(max_length=25)
    name_middle = models.CharField(max_length=25, blank=True)
    name_last = models.CharField(max_length=50)

    dancer_type = models.CharField(
        max_length=3,
        choices=DANCER_TYPE_CHOICES,
        default=PRO,
    )

    name_fix_date = models.DateField(default=date(2021,4,19))

    def __str__(self):
        if len(self.name_middle) > 0:
            return self.name_last + ", " + self.name_first + " " + self.name_middle
        else:
            return self.name_last + ", " + self.name_first

    def __lt__(self, d):
        if self.name_last == d.name_last:
            return self.name_first < d.name_first
        else:
            return self.name_last < d.name_last

    class Meta:
        ordering = ["name_last", "name_first"]
