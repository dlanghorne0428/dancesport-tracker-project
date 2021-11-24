from django.db import models
from datetime import date

# Create your models here.
class Dancer(models.Model):
    # name fields
    name_first = models.CharField(max_length=25)
    name_middle = models.CharField(max_length=25, blank=True)
    name_last = models.CharField(max_length=50)

    # dancer type has choices
    PRO = 'PRO'
    ADULT_AMATEUR = 'AM'
    JUNIOR_AMATEUR = 'JR'
    DANCER_TYPE_CHOICES = [
        (PRO, 'Professional'),
        (ADULT_AMATEUR, 'Amateur'),
        (JUNIOR_AMATEUR , 'Junior'),
    ]
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


class Couple(models.Model):
    dancer_1 = models.ForeignKey('Dancer', on_delete=models.CASCADE, related_name="leader_or_student")
    dancer_2 = models.ForeignKey('Dancer', on_delete=models.CASCADE, related_name="follower_or_instructor")

    # Couple type has choices
    PRO_COUPLE = 'PRC'
    PRO_AM_COUPLE = 'PAC'
    JR_PRO_AM_COUPLE = 'JPC'
    AMATEUR_COUPLE = 'AMC'
    JR_AMATEUR_COUPLE = 'JAC'
    COUPLE_TYPE_CHOICES = [
        (PRO_COUPLE, 'Professionals'),
        (PRO_AM_COUPLE, 'Pro-Am'),
        (JR_PRO_AM_COUPLE , 'Junior_Pro-Am'),
        (AMATEUR_COUPLE, 'Amateurs'),
        (JR_AMATEUR_COUPLE , 'Junior_Amateurs'),
    ]
    couple_type = models.CharField(
        max_length=3,
        choices=COUPLE_TYPE_CHOICES,
        default=PRO_AM_COUPLE,
    )

    def __str__(self):
        return self.dancer_1.__str__() + " and " + self.dancer_2.__str__()

    def __lt__(self, c):
        if self.dancer_1 == c.dancer_1:
            if self.dancer_2 == c.dancer_2:
                return self.couple_type < c.couple_type
            else:
                return self.dancer_2 < c.dancer_2
        else:
            return self.dancer_1 < c.dancer_1

    class Meta:
        ordering = ["dancer_1"]
