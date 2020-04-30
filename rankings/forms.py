from django.db import models
from django.forms import ModelForm, ModelChoiceField
from .models import Dancer, Couple

class DancerForm(ModelForm):
    class Meta:
        model = Dancer
        fields = ['name_first', 'name_middle', 'name_last', 'dancer_type']

class CoupleForm(ModelForm):
    dancer_1 = ModelChoiceField(queryset=Dancer.objects.order_by('name_last'))
    dancer_2 = ModelChoiceField(queryset=Dancer.objects.order_by('name_last'))
    # couple_type_field = models.CharField(max_length = 3, choices=Couple.COUPLE_TYPE_CHOICES)
    class Meta:
        model = Couple
        fields = ['dancer_1', 'dancer_2', 'couple_type']
