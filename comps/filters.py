import django_filters
from django import forms
from .models.heat import Heat

class HeatFilter(django_filters.FilterSet):

    info = django_filters.CharFilter(lookup_expr='icontains')
    heat_number = django_filters.NumberFilter(widget=forms.TextInput(attrs={'size': 5}))
    base_value = django_filters.NumberFilter(widget=forms.TextInput(attrs={'size': 5}))

    class Meta:
        model = Heat
        fields = ['category', 'style' ]
