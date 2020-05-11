from django.db import models

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

    def __str__(self):
        if len(self.name_middle) > 0:
            return self.name_last + ", " + self.name_first + " " + self.name_middle
        else:
            return self.name_last + ", " + self.name_first


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
        (PRO_COUPLE, 'Professional_Couple'),
        (PRO_AM_COUPLE, 'Pro-Am_Couple'),
        (JR_PRO_AM_COUPLE , 'Junior_Pro-Am_Couple'),
        (AMATEUR_COUPLE, 'Amateur_Couple'),
        (JR_AMATEUR_COUPLE , 'Junior_Amateur_Couple'),
    ]
    couple_type = models.CharField(
        max_length=3,
        choices=COUPLE_TYPE_CHOICES,
        default=PRO_AM_COUPLE,
    )

    # fields for rankingg
    event_count = models.IntegerField(default=0)
    total_points = models.FloatField(default=0.0)
    rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.dancer_1.__str__() + " and " + self.dancer_2.__str__()
