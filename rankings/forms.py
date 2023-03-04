from django import forms
from django.db import models
from django.forms import Form, ModelForm, ModelChoiceField
from .models.dancer import Dancer
from .models.couple import Couple
from .models.elo_rating import EloRating

class EloRatingForm(ModelForm):
    class Meta:
        model = EloRating
        fields = ['num_events', 'value']  

class DancerForm(ModelForm):
    class Meta:
        model = Dancer
        fields = ['name_first', 'name_middle', 'name_last', 'dancer_type']


class CoupleTypeForm(ModelForm):
    # this is a simple form used to select a couple_type 
    class Meta:
        model = Couple
        fields = ['couple_type']


class CoupleForm(ModelForm):
    # this form is used when creating or editing a couple based on dancer names
    dancer_1 = ModelChoiceField(queryset=Dancer.objects.all())
    dancer_2 = ModelChoiceField(queryset=Dancer.objects.all())
    
    class Meta:
        model = Couple
        fields = ['dancer_1', 'dancer_2', 'couple_type']

    def __init__(self, couple_type=None, dancer_position = None, dancer_id = None, dancer_type = None, partner_id = None, **kwargs):
        super(CoupleForm, self).__init__(**kwargs)
        if couple_type is None:
            pass
        else:
            self.fields['couple_type'].initial = couple_type
            # populate the choice fields of the form based on the couple_type
            if couple_type == Couple.PRO_COUPLE:
                if dancer_position == 1:
                    self.fields['dancer_1'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    self.fields['dancer_1'].initial = dancer_id
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    if partner_id is not None:
                        self.fields['dancer_2'].initial = partner_id
                else:
                    self.fields['dancer_1'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    self.fields['dancer_2'].initial = dancer_id
            elif couple_type == Couple.PRO_AM_COUPLE:
                if dancer_position == 1:
                    self.fields['dancer_1'].queryset = Dancer.objects.exclude(dancer_type=Dancer.PRO)
                    self.fields['dancer_1'].initial = dancer_id
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    if partner_id is not None:
                        self.fields['dancer_2'].initial = partner_id
                else:
                    self.fields['dancer_1'].queryset = Dancer.objects.exclude(dancer_type=Dancer.PRO)
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    self.fields['dancer_2'].initial = dancer_id
            elif couple_type == Couple.AMATEUR_COUPLE:
                if dancer_position == 1:
                    self.fields['dancer_1'].queryset = Dancer.objects.exclude(dancer_type=Dancer.PRO)
                    self.fields['dancer_1'].initial = dancer_id
                    self.fields['dancer_2'].queryset = Dancer.objects.exclude(dancer_type=Dancer.PRO)
                    if partner_id is not None:
                        self.fields['dancer_2'].initial = partner_id
                else:
                    self.fields['dancer_1'].queryset = Dancer.objects.exclude(dancer_type=Dancer.PRO)
                    self.fields['dancer_2'].queryset = Dancer.objects.exclude(dancer_type=Dancer.PRO)
                    self.fields['dancer_2'].initial = dancer_id
            elif couple_type == Couple.JR_PRO_AM_COUPLE:
                if dancer_position == 1:
                    self.fields['dancer_1'].queryset = Dancer.objects.filter(dancer_type=Dancer.JUNIOR_AMATEUR)
                    self.fields['dancer_1'].initial = dancer_id
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    if partner_id is not None:
                        self.fields['dancer_2'].initial = partner_id
                else:
                    self.fields['dancer_1'].queryset = Dancer.objects.filter(dancer_type=Dancer.JUNIOR_AMATEUR)
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.PRO)
                    self.fields['dancer_2'].initial = dancer_id
            else:  #couple_type == Couple.JUNIOR_AMATEUR
                if dancer_position == 1:
                    self.fields['dancer_1'].queryset = Dancer.objects.filter(dancer_type=Dancer.JUNIOR_AMATEUR)
                    self.fields['dancer_1'].initial = dancer_id
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.JUNIOR_AMATEUR)
                    if partner_id is not None:
                        self.fields['dancer_2'].initial = partner_id
                else:
                    self.fields['dancer_1'].queryset = Dancer.objects.filter(dancer_type=Dancer.JUNIOR_AMATEUR)
                    self.fields['dancer_2'].queryset = Dancer.objects.filter(dancer_type=Dancer.JUNIOR_AMATEUR)
                    self.fields['dancer_2'].initial = dancer_id


class CoupleSelectForm(Form):
    # this form is used to select an existing couple from the list of all couples
    name         = forms.CharField(label="Last Name", required=False)
    couple_type  = forms.ChoiceField(choices=[("", "-------")] + Couple.COUPLE_TYPE_CHOICES, required=False)
    name.widget.attrs.update(size='25', placeholder='dancer-last-name')    
