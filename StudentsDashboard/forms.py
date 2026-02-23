from django import forms
from .models import Report, Message, ReportCategory

class ReportForm(forms.ModelForm):
    incident_date = forms.DateField(
        input_formats=['%d %B %Y'],
        error_messages={
            'invalid': 'Date format is 01 January 1996.'
        }
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ReportCategory.objects.all().order_by('name')
        if not self.fields['category'].queryset.exists():
            self.fields['category'].required = False
        self.fields['incident_date'].widget.attrs.update({
            'placeholder': '01 January 1996'
        })

    class Meta:
        model = Report
        fields = ['category','title','description','incident_date','location']

class TrackForm(forms.Form):
    tracking_token = forms.CharField(max_length=8)

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
