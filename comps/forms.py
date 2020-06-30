from django.forms import ModelForm
from .models.comp import Comp

class CompForm(ModelForm):
    class Meta:
        model = Comp
        fields = ['title', 'location', 'start_date', 'end_date', 'logo', 'url_data_format', 'heatsheet_url', 'scoresheet_url']

from .models.heat import Heat
class HeatForm(ModelForm):
    class Meta:
        model = Heat
        fields = ['info', 'category', 'heat_number', 'extra', 'style', 'base_value']

from .models.heat_entry import Heat_Entry
class HeatEntryForm(ModelForm):
    class Meta:
        model = Heat_Entry
        fields = ['shirt_number', 'result', 'points']
