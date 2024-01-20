from django import forms
from core.models import SEMESTER, Session, Student, ResultUploadBulk, ResultUploadSingle, Course

class Form(forms.Form):
    session = forms.ModelChoiceField(queryset=None)
    semester = forms.ChoiceField(choices=SEMESTER.choices)
    def __init__(self, *args, **kwargs):
        super(). __init__(*args, **kwargs)
        queryset = Session.objects.all().order_by('-name')
        self.fields['session'].queryset = queryset

class AddStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ['user','approved','date_created','date_approved']

class ResultUploadBulkForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['course'].queryset = Course.objects.filter(department = request.usertype.department)
    class Meta:
        model = ResultUploadBulk
        exclude = ['approved','approved_by','date_created','date_updated']

class ResultUploadSingleForm(forms.ModelForm):
    def __init__(self,request,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['course'].queryset = Course.objects.filter(department = request.usertype.department)
    class Meta:
        model = ResultUploadSingle
        exclude = ["approve","approved_by", "date_created","date_updated"]