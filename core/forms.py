from typing import Any
from rolepermissions.checkers import has_role

from django import forms
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from .models import User

class LoginVerificationForm(forms.Form):
    code = forms.CharField()
    def __init__(self,server_code,*args, **kwargs):
        super().__init__(*args,**kwargs)
        self.server_code = server_code
        
    def clean(self):
        if self.cleaned_data['code'] != self.server_code:
            raise forms.ValidationError("Code is incorrect")

class StudentLoginForm(forms.Form):
    email = forms.EmailField()
    def clean(self):
        user = User.objects.filter(email = self.cleaned_data['email'])
        if not user.exists():
            raise forms.ValidationError("Student deos not exists")
        if not has_role(user[0],'student'):
            raise forms.ValidationError("Student deos not exists")

        return super().clean()
    def get_user(self):
        return User.objects.get(email = self.cleaned_data['email'])
    



class AdminLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    def __init__(self,request,*args,**kwargs):
        self.request = request
        self.user = None
        super().__init__(*args,**kwargs)
    def clean(self):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        self.user = authenticate(self.request,email = email, password = password)
        if not self.user:
            raise forms.ValidationError("Invalid Credentatial")
        return self.cleaned_data
    def get_user(self):
        return self.user
    def send_login_code(self,code):
        email_address = self.cleaned_data['email']
        message = f"""
A login request has been made to your grademe account. contact support if it is not you.
Verification Code : {code}
"""
        send_mail("GradeMe Login",message,"admin@grademe.com",[email_address], fail_silently=True)
