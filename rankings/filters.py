import django_filters
from .models import Dancer

class DancerFilter(django_filters.FilterSet):
    name_last = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Dancer
        fields = ['dancer_type']
