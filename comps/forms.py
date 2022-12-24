from django import forms
from django.forms import Form, ModelForm

from .models.comp import Comp

class CompForm(ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}))
    location = forms.CharField(widget=forms.TextInput(attrs={'size': '25'}))    
    heatsheet_url = forms.CharField(widget=forms.TextInput(attrs={'size': '75'}))
    scoresheet_url = forms.CharField(widget=forms.TextInput(attrs={'size': '75'}))
    class Meta:
        model = Comp
        fields = ['title', 'location', 'start_date', 'end_date', 'url_data_format', 'heatsheet_url', 'scoresheet_url']

class CompTitleForm(ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'size': '60'}))
    class Meta:
        model = Comp
        fields = ['title']

from .models.heat import Heat
class HeatForm(ModelForm):
    initial_elo_value = forms.IntegerField(label='Elo Value', required=False)
    class Meta:
        model = Heat
        fields = ['info', 'category', 'heat_number', 'extra', 'dance_off', 'style', 'base_value',  'initial_elo_value']

from .models.heat_entry import Heat_Entry
class HeatEntryForm(ModelForm):
    class Meta:
        model = Heat_Entry
        fields = ['shirt_number', 'result', 'points']


class CompCoupleForm(Form):
    name = forms.CharField(label="Last Name", required=False)
    number = forms.CharField(label="Shirt Number", required=False)

    name.widget.attrs.update(size='25', placeholder='dancer-last-name')    
    number.widget.attrs.update(size='5')
    

from .models.heatlist_dancer import Heatlist_Dancer
class HeatListDancerForm(Form):
    name = forms.CharField(label="Last Name", required=False)
    alias = forms.CharField(label="Alias Last Name", required=False)
    comp = forms.CharField(label="Comp Name", required=False)    
    
    name.widget.attrs.update(size='20', placeholder='dancer-last-name')   
    alias.widget.attrs.update(size='20', placeholder='dancer-alias-name')   
    comp.widget.attrs.update(size='20', placeholder='comp-name')   