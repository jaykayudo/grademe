from django.db.models.query import QuerySet
from django.shortcuts import render

# Create your views here.
from typing import Any
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, FileResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, View, ListView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.db.models import Count
from django.core import cache

from core.forms import LoginVerificationForm,StudentLoginForm
from core.tools import generate_code, send_login_code, calculate_gpa, download_result
from core.models import User, Student, Notification, Grade, SupportMessage, GradeReport, Session
from core.mixins import StudentStatus
from .forms import CheckResultForm, GradeReportForm, SupportMessageForm


# Create your views here.
class StudentLoginView(FormView):
    """
    View for the student passwordless login. sends code to complete login.
    url: /student/login/
    """
    form_class = StudentLoginForm
    template_name = "student/student-login.html"
    success_url = reverse_lazy("student:login_verify")

    def get(self, request: HttpRequest, *args: str, **kwargs: Any):
        if request.user.is_authenticated:
            return redirect("student:dashboard")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        self.request.session['user_id'] = user.id
        code = generate_code()
        self.request.session['login_code'] = str(code)
        send_login_code(user.email,code)
        messages.success(self.request,"Login Verification Code has been sent to your email.")
        return super().form_valid(form)
    
class StudentLoginVerifyView(FormView):
    """
    View for the student login verification.
    url: /student/login/verify/
    """
    form_class = LoginVerificationForm
    template_name = "student/student-login-verify.html"
    success_url = reverse_lazy("student:dashboard")
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['server_code'] = self.request.session['login_code']
        return form_kwargs

    def get(self, request: HttpRequest, *args: str, **kwargs: Any):
        if request.user.is_authenticated:
            return redirect("student:dashboard")
        if not request.session.get("user_id") or not request.session.get("login_code"):
            return redirect("student:login")
        return super().get(request, *args, **kwargs)

    def form_valid(self,form):
        
        user = User.objects.get(id = int(self.request.session.get("user_id")))
        login(self.request,user)
        messages.success(self.request, "Login Successful")
        del self.request.session['user_id']
        del self.request.session['login_code']
        return super().form_valid(form)
def resend_login_code(request):
    """
    View for re-sending the login verification email. return an error if login verification request was not made.
    url:  /student/login/resend-code/
    """
    code = request.session.get('login_code')
    user_id = request.session.get('user_id')
    
    if code and user_id:
        user = User.objects.get(id = int(user_id))
        email = user.email
        send_login_code(email,str(code))
        messages.success(request,"Login Code Resent")
        if "next" in request.GET:
            return redirect(request.GET['next'])
        else:
            return redirect(reverse("student:login_verify"))
    else:
        return HttpResponseBadRequest()
def logout_user(request):
    """
    Logout view: for logging the student out of the dashboard
    url: /student/logout/
    """
    logout(request)
    messages.success(request,"Logout Successful")
    return redirect("student:login")

class ProfileView(StudentStatus,View):
    def get(self,request):
        student = Student.objects.get(id = request.user.student.id)
        context = {
            'student': student
        }
        return render(request,"student/student-profile.html", context)
    
class DashboardView(StudentStatus, View):
    """
    View for student dashboard
    context: Student GPA, Number of Session Result, Latest result upload session, Latest result upload semester
    Latest Notification
    url: /student/dashboard/
    """
    def get(self,request):
        """
        Use Django cache
        """
        student = request.user.student
        
        cgpa = student.calculate_cgpa()
        number_of_session = Grade.objects.filter(student = student).values("session").annotate(session_count = Count("session")).count()
        latest_result_pair = Grade.objects.filter(student = student).order_by("-session","-semester")
        latest_session = latest_result_pair[0].session if latest_result_pair else "None"
        latest_semester = latest_result_pair[0].get_semester_display() if latest_result_pair else "None"
        latest_notification = Notification.objects.filter(user = request.user).order_by("-date")[:10]

        context = {
            'cgpa': cgpa,
            'number_of_session': number_of_session,
            'latest_session': latest_session,
            'latest_semester': latest_semester,
            'latest_notification': latest_notification
        }
        return render(request, "student/student-home.html",context)

class CheckResultView(StudentStatus,View):
    """
    View for student result checking
    post data: session, semester
    url: /student/check-result/
    """
    def get(self,request):
        form = CheckResultForm()
        return render(request, "student/student-check-result.html", {'form':form})
    def post(self,request):
        form = CheckResultForm(request.POST)
        if not form.is_valid():
            return render(request, "student/student-check-result.html",{'form':form})
        data = form.cleaned_data
        student = request.user.student;
        session = Session.objects.get(id = data['session'])
        semester = int(data['semester'])
        grade = Grade.objects.filter(student = student,session = session, semester = semester).order_by("date_created")
        gpa = calculate_gpa(grade)
        context = {
            'grades': grade,
            'gpa': gpa,
            'session': session,
            'semester': semester,
            'student': student
        }
        Notification.objects.create(user = request.user,title="Result Check", 
                                    message = f"You checked your {session} session {semester} semester result.")
        return render(request,"student/student-result.html", context)

class DownloadResultView(StudentStatus, View):
    """
    View to download student result to pdf.
    url:/student/check-result/download/?session=<int>&semester=<int>
    """
    def get(self,request):
        semester = request.GET.get("semester")
        session_id = request.GET.get("session")
        if not semester or not session_id:
            messages.error(request,"No semester or session specified")
        
        session = Session.objects.get(id = int(session_id))
        student = request.user.student
        file = download_result(student, int(semester),session)
        return FileResponse(file,filename="{student.last_name}-result.pdf")


class GradeReportView(StudentStatus, View):
    """
    View for reporting a grade if it doesn't sit well with the student.
    url: /student/check-result/report/<grade_id>/
    """
    def get(self,request,id):
        grade = Grade.objects.get(id = id)
        form = GradeReportForm()
        return render(request,"student/student-grade-report.html", {'form':form,'grade':grade})

    def post(self, request,id):
        grade = Grade.objects.get(id = id)
        form = GradeReportForm(request.POST)
        if not form.is_valid():
            return render(request,"student/student-grade-report.html", {'form':form,'grade':grade})
        GradeReport.objects.create(grade = grade,department = request.user.student.department,message = form.cleaned_data['message'])
        messages.success(self.request, f"your report for {grade.course} has been sent successfully")
        Notification.objects.create(user = self.request.user,title="Grade Report",message = f"your report for {grade.course} has been sent successfully")
        return super().form_valid(form)

class SupportMessageView(StudentStatus,FormView):
    """
    View for sending messages to support.
    post-data: title, message
    url: /student/support/
    """
    form_class = SupportMessageForm
    template_name = "student/student-support.html"
    success_url = reverse_lazy('student:support')

    def form_valid(self, form):
        obj = form.save(commit =False)
        obj.student = self.request.usertype
        obj.department = self.request.usertype.department
        obj.save()
        messages.success(self.request,"Support Message sent. you will be reached via email")
        Notification.objects.create(user = self.request.user,title = "Support Message", 
                                    message=f"Your Message of title f{obj.title} was sent to the support")
        return super().form_valid(form)

class NotificationListView(StudentStatus,ListView):
    paginate_by = 30
    template_name = "student/student-notification.html"
    def get_queryset(self):
        return Notification.objects.filter(user = self.request.user).order_by("-date")

