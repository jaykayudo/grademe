from django import forms
from core.models import SEMESTER, Session, GradeReport, SupportMessage

class CheckResultForm(forms.Form):
    session = forms.ModelChoiceField(queryset=None)
    semester = forms.ChoiceField(choices=SEMESTER.choices)
    def __init__(self, *args, **kwargs):
        super(). __init__(*args, **kwargs)
        queryset = Session.objects.all().order_by('-name')
        self.fields['session'].queryset = queryset

class GradeReportForm(forms.ModelForm):
    class Meta:
        model = GradeReport
        fields = ['grade','department','message']

class SupportMessageForm(forms.ModelForm):
    class Meta:
        model = SupportMessage
        fields = ['title','message']