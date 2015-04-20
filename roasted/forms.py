from django.forms import ModelForm, TextInput
from models import Target

class TargetForm(ModelForm):

    class Meta:
        model = Target
        fields = ['key','target_url']
        widgets = {
            'key': TextInput(attrs={'class': 'form-control'}),
            'target_url': TextInput(attrs={'class': 'form-control', 'size':'150'})
        }
