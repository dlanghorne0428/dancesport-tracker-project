from django.forms import ModelForm
from .models import Comp

class CompForm(ModelForm):
    class Meta:
        model = Comp
        fields = ['title', 'location', 'start_date', 'end_date', 'logo', 'url_data_format', 'heatsheet_url', 'scoresheet_url']
