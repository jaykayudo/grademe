from typing import Any
from django import forms
from core.models import Student, User, Department, Admin


class AddStudentForm(forms.ModelForm):
    def __init__(self,chiefadmin,*args,**kwargs):
        self.chiefadmin = chiefadmin
        super().__init__(*args,**kwargs)
    
    class Meta:
        model = Student
        exclude = ['user','approved','date_created','date_approved','created_by']
    def clean(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email = email).exists():
            raise forms.ValidationError("User email already exists")
        chiefadmin_departments = Department.objects.filter(faculty = self.chiefadmin.faculty)
        if self.cleaned_data['department'] not in chiefadmin_departments:
            raise forms.ValidationError("Invalid Department")
        return super().clean()

class AddAdminForm(forms.ModelForm):
    def __init__(self,chiefadmin,*args,**kwargs):
        self.chiefadmin = chiefadmin
        super().__init__(*args,**kwargs)
    
    class Meta:
        model = Admin
        exclude = ['user','approved','date_created','date_approved']
    def clean(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email = email).exists():
            raise forms.ValidationError("User email already exists")
        chiefadmin_departments = Department.objects.filter(faculty = self.chiefadmin.faculty).values_list("id", flat=True)
        if self.cleaned_data['department'] not in chiefadmin_departments:
            raise forms.ValidationError("Invalid Department")
        return super().clean()