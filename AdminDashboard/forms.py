from django import forms
from StudentsDashboard.models import Message, Report

class AdminMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']


class ReportUpdateForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['status', 'severity']
