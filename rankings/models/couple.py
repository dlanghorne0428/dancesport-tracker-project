from django.db import models
from .dancer import Dancer

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
        (PRO_COUPLE, 'Professional'),
        (PRO_AM_COUPLE, 'Pro-Am'),
        (JR_PRO_AM_COUPLE , 'Junior Pro-Am'),
        (AMATEUR_COUPLE, 'Amateur'),
        (JR_AMATEUR_COUPLE , 'Junior Amateur'),
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
