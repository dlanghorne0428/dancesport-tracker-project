import django_filters
from django import forms
from .models import Dancer

class DancerFilter(django_filters.FilterSet):
    name_last = django_filters.CharFilter(lookup_expr='icontains', widget=forms.TextInput(attrs={'size':12}))

    class Meta:
        model = Dancer
        fields = ['dancer_type']
