from django.forms import ModelForm
from .models import Dancer, Couple

class DancerForm(ModelForm):
    class Meta:
        model = Dancer
        fields = ['name_first', 'name_middle', 'name_last', 'dancer_type']

class CoupleForm(ModelForm):
    class Meta:
        model = Couple
        fields = ['dancer_1', 'dancer_2', 'couple_type']
