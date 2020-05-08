from django.forms import ModelForm
from .models import Comp

class CompForm(ModelForm):
    class Meta:
        model = Comp
        fields = ['title', 'location', 'start_date', 'end_date', 'logo', 'url_data_format', 'heatsheet_url', 'scoresheet_url']

from .models import Heat
class HeatForm(ModelForm):
    class Meta:
        model = Heat
        fields = ['info', 'heat_number', 'rounds', 'style', 'base_value']
