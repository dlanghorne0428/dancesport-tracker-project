from django.db import models
from .couple import Couple
from comps.models.heat import DANCE_STYLE_CHOICES


class EloRating(models.Model):
    couple = models.ForeignKey('Couple', on_delete=models.CASCADE)
    style = models.CharField(max_length = 4, choices = DANCE_STYLE_CHOICES, default="UNK")
    num_events = models.IntegerField(default=0)
    value = models.FloatField(null=True, default=None)
    
    def __str__(self):
        return str(self.couple) + " - " + self.style + ": " + str(round(self.value, 2))
    
    def __lt__(self, v):
        return self.value < v