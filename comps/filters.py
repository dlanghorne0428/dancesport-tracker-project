import django_filters
from .models import Heat

class HeatFilter(django_filters.FilterSet):

    info = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Heat
        fields = ['category', 'style', 'heat_number', 'base_value'  ]
