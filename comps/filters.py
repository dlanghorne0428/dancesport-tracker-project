import django_filters
from django import forms
from .models.comp import Comp
from .models.heat import Heat, DANCE_STYLE_CHOICES

class CompFilter(django_filters.FilterSet):

    title = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':18}))
    location = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':12}))
    process_state = django_filters.ChoiceFilter(choices=Comp.PROCESS_STATE_CHOICES, empty_label="Any Status") 


class HeatFilter(django_filters.FilterSet):

    info = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':16, 'placeholder':'keyword'}))
    heat_number = django_filters.NumberFilter(widget=forms.TextInput(attrs={'size': 5}))
    style = django_filters.ChoiceFilter(choices=DANCE_STYLE_CHOICES, empty_label="All Styles") 
    category = django_filters.ChoiceFilter(choices=Heat.CATEGORY_CHOICES, empty_label="ALL")

