from django.shortcuts import render

# Create your views here.
from typing import Any
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, FileResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.views.generic import View, ListView, FormView, DetailView
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Count
from django.forms import formset_factory
from django.views.decorators.cache import cache_page

from core.forms import AdminLoginForm, LoginVerificationForm,StudentLoginForm
from core.tools import generate_code, send_login_code, send_code, calculate_gpa, download_result
from core.models import User, Admin, Student, ResultUploadBulk, ResultUploadSingle, SupportMessage, GradeReport, Grade, Notification \
,Action, Session, STATUS
from core.mixins import AdminStatus
from .forms import AddStudentForm, ResultUploadBulkForm, ResultUploadSingleForm

# Create your views here.
class AdminLoginView(FormView):
    """
    View for the admin login
    url: /admin/login/
    """
    form_class = AdminLoginForm
    template_name = "normaladmin/admin-login.html"
    success_url = reverse_lazy("normaladmin:login_verify")
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    def get(self, request: HttpRequest, *args: str, **kwargs: Any):
        if request.user.is_authenticated:
            return redirect("normaladmin:dashboard")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        self.request.session['user_id'] = user.id # Save the user id in session
        code = generate_code() # Generate a 6 digit code
        self.request.session['login_code'] = str(code) # Store the code in a session
        send_login_code(user.email,code) # Send the code to the user 
        messages.success(self.request,"Login Verification Code has been sent to your email.")
        return super().form_valid(form)
    
class AdminLoginConfirmView(FormView):
    """
    View for the verification of login with code
    url: /admin/login/verify/
    """
    form_class = LoginVerificationForm # verificaition form class
    template_name = "normaladmin/admin-login-verify.html"
    success_url = reverse_lazy("normaladmin:dashboard")
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        # send to code to the form so that the form can use it for verification
        # The code verification is done in the form
        form_kwargs['server_code'] = self.request.session['login_code'] 
        return form_kwargs

    def get(self, request: HttpRequest, *args: str, **kwargs: Any):
        # Prevent authenticated user from accessing this view
        if request.user.is_authenticated:
            return redirect("normaladmin:dashboard")
        # Prevent user from accessing this view if user id and code is not found in the session
        if not request.session.get("user_id") or not request.session.get("login_code"):
            return redirect("normaladmin:login")
        return super().get(request, *args, **kwargs)

    def form_valid(self,form):
        
        user = User.objects.get(id = int(self.request.session.get("user_id")))
        login(self.request,user) # Login the admin
        messages.success(self.request, "Login Successful")
        # Delete code and user id from session after logging in is done
        del self.request.session['user_id']
        del self.request.session['login_code']
        if user.admin.temp_pass:
            # if the admin  has temporary password, redirect admin to change password view
            messages.warning(self.request,"You are using a temporary password. it is advisable to change your password.")
            self.success_url = reverse("normaladmin:change_password")
        return super().form_valid(form)
def resend_login_code(request):
    """
    View to resend the login code to user email
    url: /admin/login/verify/resend-code/
    """
    code = request.session.get('login_code')
    user_id = request.session.get('user_id')
    
    # Prevent user from accessing this view if user id and code is not found in the session
    if code and user_id:
        user = User.objects.get(id = int(id))
        email = user.email
        send_login_code(email,str(code)) #resend code
        messages.success(request,"Login Code Resent")
        if "next" in request.GET:
            return redirect(request.GET['next'])
        else:
            return redirect(reverse("normaladmin:login_verify"))
    else:
        # return a 400 error if code and user id is not found
        return HttpResponseBadRequest()

def logout_user(request):
    """
    View for logging out the user from dashboard
    url: /admin/logout/
    """
    logout(request)
    messages.success(request,"Logout Successful")
    return redirect("normaladmin:login")
class ChangePassword(AdminStatus,PasswordChangeView):
    """
    View for changing the password of the admin. inheriting django.contrib.auth password change view
    for this.
    url: /admin/profile/change-password/
    """
    template_name = "normaladmin/admin-change-password.html"
    success_url = reverse_lazy("normaladmin:change-password")
    def form_valid(self,form):
        admin = self.request.user.admin
        if admin.temp_pass:
            # set temp pass to false to clarify that the admin is no longing using a temp paswword
            admin.temp_pass = False
            admin.save()
        messages.success(self.request,"Password Changed")
        return super().form_valid(form)

class ProfileView(AdminStatus,View):
    """
    View for viewing the profile details of the admin.
    url: /admin/profile/
    """
    # @cache_page(900)
    def get(self,request):
        admin = Admin.objects.get(id = request.user.admin.id)
        return render(request,"normaladmin/admin-profile.html", {'admin':admin})

class DashboardView(AdminStatus,View):
    """
    View for the admin Dashboard of the admin. 
    Caching is used here as a lot of database interaction and connection was done here
    which might slow the performance
    url: /admin/dashboard/ 
    """
    @cache_page(900)
    def get(self,request):
        admin = Admin.objects.get(id = request.user.admin.id) # Get the current admin instance
        number_of_uploaded_grades = Grade.objects.filter(uploaded_by = admin).count() # Get the count of all the grades uploaded by this admin
        latest_notification = Notification.objects.filter(user = request.user).order_by("-date")[:10] # This admin latest notification
        number_of_students = Student.objects.filter(department = admin.department).count() # The number of student in this admin's department
        # The number of result that the current admin uploaded that has not been approved
        number_of_unapproved_result = ResultUploadBulk.objects.filter(uploaded_by = admin, status = STATUS.PENDING).count() +\
                                          ResultUploadSingle.objects.filter(uploaded_by = admin, status = STATUS.PENDING).count()
        # the latest actions that this admin has done on this system.
        latest_actions = Action.objects.filter(user = request.user).order_by('-date')[:10]
        context = {
            'admin': admin,
            'number_of_uploaded_grades':number_of_uploaded_grades,
            'latest_notification':latest_notification,
            'number_of_students':number_of_students,
            'number_of_unapproved_result':number_of_unapproved_result,
            'latest_actions':latest_actions,
        }
        return render(request,"normaladmin/admin-home.html", context)


class NotificationListView(AdminStatus,ListView):
    """
    View for viewing all notification with pagination. inheriting list view fior this.
    url: /admin/notification/
    """
    paginate_by = 30
    template_name = "normaladmin/admin-notification.html"
    def get_queryset(self):
        return Notification.objects.filter(user = self.request.user).order_by("-date")
    
class GradeReportListView(AdminStatus, ListView):
    """
    View for viewing all the grade reports made by the students
    url: /admin/messages/grade-report/
    """
    paginate_by = 100
    template_name = "normaladmin/admin-grade-report.html"
    def get_queryset(self):
        # Filter it by the department that of the admin
        # usertype returns the instance of the type of user the current user is i.e admin, chiefadmin or student
        return GradeReport.objects.filter(department = self.request.usertype.department).select_related("grade").order_by("-date_created")

class GradeReportDetailView(AdminStatus, DetailView):
    """
    View for viewing the details of a grade report
    url: /admin/messages/grade-report/<int:id>/
    """
    model = GradeReport
    template_name = "normaladmin/admin-grade-report-detail.html"
    pk_url_kwarg = "id"
    def get(self,request, *args,**kwargs):
        object = self.get_object()
        # Check whether the report belongs to the admin's department
        if object.department != self.request.user.admin.department:
            return HttpResponseForbidden() # return 403 error if the report is not for the admin's department
        return super().get( request,*args, **kwargs)

class SupportListView(AdminStatus, ListView):
    """
    View for viewing all the support messages made by students in the admin's department.
    url: /admin/messages/support-messages/
    """
    paginate_by = 100
    template_name = "normaladmin/admin-support.html"
    def get_queryset(self):
        return SupportMessage.objects.filter(department = self.request.user.admin.department).order_by("-date")

class SupportDetailView(AdminStatus, DetailView):
    """
    View for viewing the details of a support message
    url: /admin/messages/support-messages/<int:id>/
    """
    model = SupportMessage
    template_name = "normaladmin/admin-support-detail.html"
    pk_url_kwarg = "id"
    def get(self,request, *args,**kwargs):
        object = self.get_object()
        # Check whether the support message belongs to the admin's department
        if object.department != self.request.user.admin.department:
            return HttpResponseForbidden() # return 403 error if the support message is not for the admin's department
        return super().get( request,*args, **kwargs)


class UploadHistoryListView(AdminStatus, ListView):
    """
    View for viewing all the result uploads made by the current admin. both bulks and singles.
    url: /admin/result/upload-history/
    """
    paginate_by = 100
    template_name = "normaladmin/admin-grade-report.html"
    def get_queryset(self):
        admin = self.request.user.admin
        qs_list = [*ResultUploadBulk.objects.filter(uploaded_by= admin).annotate(type="bulk"),
                   *ResultUploadSingle.objects.filter(uploaded_by= admin).annotate(type="single")]
        qs_list.sort(key=lambda x: x.date_created, reverse=True) # sort the combination of bulk and single queryset by the date created
        return qs_list
    

class StudentListView(AdminStatus, ListView):
    """
    View for viewing all the students in the admin's department.
    url: /admin/student/
    """
    template_name = "normaladmin/admin-student-list.html"
    paginate_by = 50
    def get_queryset(self):
        return Student.objects.filter(department = self.request.usertype.department)
    
class StudentDetailView(AdminStatus, DetailView):
    """
    View for viewing the details of a student in the admin's department
    url: /admin/student/<int:id>/
    """
    model = Student
    template_name = "normaladmin/admin-student-detail.html"
    pk_url_kwarg = "id"
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        student = self.get_object()
        grade_list = Grade.objects.filter(student = student).values("session").annotate(session_count = Count("session")).order_by("session")
        data['grades'] = grade_list
        return data
    def get(self,request, *args,**kwargs):
        object = self.get_object()
        if object.department != self.request.user.admin.department:
            return HttpResponseForbidden()
        return super().get( request,*args, **kwargs) 

class CheckResultView(AdminStatus,View):
    """
    View for viewing a student session and semester result
    url: /admin/student/<int:id>/<int:session_id>/<int:semester>/
    """
    def get(self,request,student_id,session_id,semester):
        student = Student.objects.get(id = student_id)
        if student.department != request.user.admin.department:
            return HttpResponseForbidden()
        session = Session.objects.get(id = session_id)
        semester = int(semester)
        grade = Grade.objects.filter(student = student,session = session, semester = semester).order_by("date_created")
        gpa = calculate_gpa(grade)
        context = {
            'grades': grade,
            'gpa': gpa,
            'session': session,
            'semester': semester,
            'student': student
        }
        # Notification.objects.create(user = request.user,title="Result Check", 
        #                             message = f"You checked your {session} session {semester} semester result.")
        return render(request,"normaladmin/admin-student-result.html", context)

class DownloadResultView(AdminStatus, View):
    """
    View to download a student result to pdf.
    url:/admin/student/<id>/result-download/?session=<int>&semester=<int>
    """
    def get(self,request):
        semester = request.GET.get("semester")
        session_id = request.GET.get("session")
        if not semester or not session_id:
            messages.error(request,"No semester or session specified")
        session = Session.objects.get(id = int(session_id))
        student = Student.objects.get(id = id)
        file = download_result(student, int(semester),session)
        Action.objects.get(user = request.user, message = f"Downloaded {session} {semester} semester" 
                           "of student {student.matric_number} result")
        return FileResponse(file,filename="{student.last_name}-result.pdf")
    

class StudentAddView(AdminStatus, FormView):
    """
    View for adding a student to the admin's department.
    url: /admin/student/add/
    """
    form_class = AddStudentForm
    template_name = "normaladmin/admin-student-add.html"
    success_url = reverse_lazy("normaladmin:student_add")

    def form_valid(self, form):
        obj = form.save()
        messages.success(self.request,"Student Added.. Awaiting Approval")
        # create an action for the current action performed
        Action.objects.create(user = self.request.user,title="Student Add",message = f"Added Student. Matric Number: {obj.matric_number}")
        return super().form_valid(form)

class ResultUploadBulkView(AdminStatus,FormView):
    """
    View for making a bulk result upload
    url: /admin/result/upload-bulk/
    """
    form_class = ResultUploadBulkForm
    template_name = "normaladmin/admin-result-bulk.html"
    success_url = reverse_lazy("normaladmin:result-bulk")

    def form_valid(self, form):
        obj = form.save()
        messages.success(self.request,"Result Uploaded.. Awaiting Approval")
        Action.objects.create(user = self.request.user,title="Bulk Result Upload",message = f"Uploaded bulk result for session {obj.session}, semester {obj.semester}")
        return super().form_valid(form)

class ResultUploadSingleView(AdminStatus,View):
    """
    View for making multiple single result upload
    url: /admin/result/upload-single/
    """
    def get(self,request):
        # create a formset factory for multiple form handling
        ResultFormSet = formset_factory(ResultUploadSingleForm, max_num=1) 
        return render(request,"admin/result-single.html",{'form':ResultFormSet,'max_result': 5})
    def post(self,request):
        # Incase getlist doesn't work, map request.POST data to match data format
        extra = len(request.POST.getlist(request.POST.keys()[0])) - 1 # get the number of extra forms
        ResultFormSet= formset_factory(ResultUploadSingleForm,extra=extra)
        formset = ResultFormSet(request.POST)
        if not formset.is_valid():
            return render(request,"admin/result-single.html",{'form':formset,'max_result': 5})
        for form in formset:
            form.save()
        messages.success

    def map_func(self):
        """
        for mapping request.POST data from my custom form to match formset format
        """
        pass
