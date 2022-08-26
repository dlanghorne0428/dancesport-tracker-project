from django import forms
from django.forms import Form, ModelForm
from .models.comp import Comp

class CompForm(ModelForm):
    class Meta:
        model = Comp
        fields = ['title', 'location', 'start_date', 'end_date', 'url_data_format', 'heatsheet_url', 'scoresheet_url']

from .models.heat import Heat
class HeatForm(ModelForm):
    class Meta:
        model = Heat
        fields = ['info', 'category', 'heat_number', 'extra', 'dance_off', 'style', 'base_value']

from .models.heat_entry import Heat_Entry
class HeatEntryForm(ModelForm):
    class Meta:
        model = Heat_Entry
        fields = ['shirt_number', 'result', 'points']


class CompCoupleForm(Form):
    name = forms.CharField(label="Last Name", required=False)
    number = forms.CharField(label="Shirt Number", required=False)

    name.widget.attrs.update(size='40', placeholder='dancer-last-name')    
    number.widget.attrs.update(size='5')