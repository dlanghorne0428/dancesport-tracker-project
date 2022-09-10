import django_filters
from django import forms
from .models.comp import Comp
from .models.heat import Heat

class CompFilter(django_filters.FilterSet):

    title = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':18}))
    location = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':12}))


class HeatFilter(django_filters.FilterSet):

    info = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':12}))
    heat_number = django_filters.NumberFilter(widget=forms.TextInput(attrs={'size': 5}))
    base_value = django_filters.NumberFilter(widget=forms.TextInput(attrs={'size': 5}))

    class Meta:
        model = Heat
        fields = ['category', 'style' ]
