from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.http.response import JsonResponse
from core.tools import generate_code, send_code
from core.models import User

def landing_view(request):
    return redirect(reverse("student:login"))

class CurrentEmail(LoginRequiredMixin,View):
    """
    This is an ajax view that returns a josn response.
    View to verify current email by sending a code to the current email. 
    url: /change-email/verify-current-email/
    """
    def post(self,request):
        email = request.POST['currentemail']
        if email != request.user.email:
            return JsonResponse({"message":"Invalid Email"},status = 400)
        code = generate_code()
        request.session['current_email_code'] = code
        send_code(email,code,"Verify your Current Email","Use the code below to verify your email for your grademe account. if this wasn't you, contact support.")
        return JsonResponse({"message":"code sent"})
class ConfirmCurrentEmail(LoginRequiredMixin,View):
    """
    This is an ajax view that returns a josn response.
    View to verify the code sent to the current email. 
    url: /change-email/verify-current-email-code/
    """
    def post(self,request):
        if not "current_email_code" in request.session:
            return JsonResponse({"message": "Bad Request"},status = 400)
        code = request.POST['currentcode']
        if str(code) != str(request.session['current_email_code']):
            return JsonResponse({"message": "Bad Request"},status = 400)
        request.session['current_email_confirm'] = True
        return JsonResponse({'message':"email confirmed"})
class NewEmail(LoginRequiredMixin,View):
    """
    This is an ajax view that returns a josn response.
    View to verify the new email by sending a code to the new email. 
    url: /change-email/verify-new-email/
    """
    def post(self,request):
        email = request.POST['newemail']
        if not "current_email_confirm" in request.session:
            return JsonResponse({"message":"Email not confirmed"},status = 400)
        code = generate_code()
        request.session['new_email_code'] = code
        if User.objects.filter(email = email).exists():
            return JsonResponse({"message":"Email already exists"},status = 400)
        send_code(email,code,"Verify your New Email","Use the code below to verify your new email for your grademe account. if this wasn't you, contact support.")
        return JsonResponse({"message":"code sent"})
class ChangeEmail(LoginRequiredMixin,View):
    """
    This is an ajax view that returns a josn response.
    View to verify the code sent to the new email and changing the email as well. 
    url: /change-email/verify-new-email-code/
    """
    def post(self,request):
        new_code = request.session.get("new_email_code")
        old_code = request.session.get("current_email_code")
        email_confirm = request.session.get("current_email_confirm")
        # do  not proceed if new code, old code and email confirm does not exist in session.
        if not new_code or not old_code or not email_confirm:
            return JsonResponse({"message": "Bad Request"},status = 400)
        if str(new_code) != str(request.POST['newcode']):
            return JsonResponse({'message':"Invalid Code"}, status = 400)
        new_email = request.POST['newemail']
        # Check the new email already exists in the database user table.
        if User.objects.filter(email = new_email).exists():
            return JsonResponse({"message":"Email already exists"},status = 400)
        
        user = request.user
        user.email = new_email
        user.save()
        request.usertype.email = new_email
        request.usertype.save()
        return JsonResponse({'message':"email changed"})