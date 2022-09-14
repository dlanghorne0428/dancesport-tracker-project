import django_filters
from django import forms
from .models import Dancer

class DancerFilter(django_filters.FilterSet):
    name_last = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':16, 'placeholder': 'last name'}))
    dancer_type = django_filters.ChoiceFilter(choices=Dancer.DANCER_TYPE_CHOICES, empty_label="ALL")