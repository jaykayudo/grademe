from typing import Any
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from rolepermissions.roles import assign_role

from django.http import HttpRequest, FileResponse, HttpResponse,JsonResponse,HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, View, ListView, DetailView, UpdateView, CreateView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.views.decorators.cache import cache_page
from django.conf import settings
from django.contrib.auth.views import PasswordChangeView
from django.core.paginator import Paginator

from core.forms import AdminLoginForm, LoginVerificationForm,StudentLoginForm
from core.tools import generate_code, send_login_code, generate_password, send_site_mail, download_result, calculate_gpa
from core.mixins import ChiefAdminStatus
from core.models import *
from .form import AddStudentForm, AddAdminForm
from core.tasks import upload_approved_result_bulk


class ChiefAdminLoginView(FormView):
    """
    View for the login of the chief admin
    url: /chief-admin/login/
    """
    form_class = AdminLoginForm
    template_name = "chiefadmin/chiefadmin-login.html"
    success_url = reverse_lazy("chiefadmin:login_verify")
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    def get(self, request: HttpRequest, *args: str, **kwargs: Any):
        if request.user.is_authenticated:
            return redirect("chiefadmin:dashboard")
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user() 
        self.request.session['user_id'] = user.id
        code = generate_code() # Generate Login Code
        self.request.session['login_code'] = str(code) # Save the code to session in order to confirm it
        send_login_code(user.email,code) # send the code via mail to the user
        messages.success(self.request,"Login Verification Code has been sent to your email.")
        return super().form_valid(form)
    
class ChiefAdminLoginConfirmView(FormView):
    """
    View for verifying the login
    url: /chief-admin/login/verify/
    """
    form_class = LoginVerificationForm
    template_name = "chiefadmin/chiefadmin-login-verify.html"
    success_url = reverse_lazy("chiefadmin:dashboard")
    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['server_code'] = self.request.session['login_code']
        return form_kwargs

    def get(self, request: HttpRequest, *args: str, **kwargs: Any):
        # do not allow authenticated users to proceed.
        if request.user.is_authenticated:
            return redirect("chiefadmin:dashboard")
        if not request.session.get("user_id") or not request.session.get("login_code"):
            return redirect("chiefadmin:login")
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
    View to resend the login code to user email
    url: /chief-admin/login/verify/resend-code/
    """
    code = request.session.get('login_code')
    user_id = request.session.get('user_id')
    
    if code and user_id:
        user = User.objects.get(id = int(id))
        email = user.email
        send_login_code(email,str(code))
        messages.success(request,"Login Code Resent")
        if "next" in request.GET:
            return redirect(request.GET['next'])
        else:
            return redirect(reverse("chiefadmin:login_verify"))
    else:
        return HttpResponseBadRequest()

def logout_user(request):
    """
    View for logging out the chief admin from dashboard
    url: /chief-admin/logout/
    """
    logout(request)
    messages.success(request,"Logout Successful")
    return redirect("chiefadmin:login")

class ChangePassword(ChiefAdminStatus,PasswordChangeView):
    """
    View for changing the password of the  chief admin. inheriting django.contrib.auth password change view
    for this.
    url: /chief-admin/profile/change-password/
    """
    template_name = "chiefadmin/chiefadmin-change-password.html"
    success_url = reverse_lazy("chiefadmin:change-password")
    def form_valid(self,form):
        admin = self.request.usertype
        if admin.temp_pass:
            # set temp pass to false to clarify that the admin is no longing using a temp paswword
            admin.temp_pass = False
            admin.save()
        messages.success(self.request,"Password Changed")
        return super().form_valid(form)

class ProfileView(ChiefAdminStatus,View):
    """
    View for viewing the profile details of the chief admin.
    url: /chief-admin/profile/
    """
    # @cache_page(900)
    def get(self,request):
        chiefadmin = ChiefAdmin.objects.get(id = request.user.chiefadmin.id)
        return render(request,"chiefadmin/chiefadmin-profile.html", {'chiefadmin':chiefadmin})

class DashboardView(ChiefAdminStatus,View):
    """
    View for the admin Dashboard of the chief admin. 
    Caching is used here as a lot of database interaction and connection was done here
    which might slow the performance
    url: /chief-admin/dashboard/ 
    """
    # @cache_page(900)
    def get(self,request):
        chiefadmin = request.user.chiefadmin # get the chief admin instance
        number_of_department = Department.objects.filter(faculty = chiefadmin.faculty).count() # get the number of departments in the chief admin faculty
        number_of_courses = Course.objects.filter(department__in = chiefadmin.faculty.department_set.all()).count() # get the number of departments in the chief admin faculty
        latest_notification = Notification.objects.filter(user = request.user).order_by("-date")[:10] # get the ltest notifications of the chief admin
        number_of_students = Student.objects.filter(department__in = chiefadmin.faculty.department_set.all()).count() # get the number of students in the chief admin's faculty
        number_of_unapproved_students = Student.objects.filter(department__in = chiefadmin.faculty.department_set.all(), approved=False).count() # get the number of students in the chief admin's faculty
        number_of_admins = Admin.objects.filter(department__in = chiefadmin.faculty.department_set.all()).count()
        # The number of result that has not been approved. both bulk and singles
        number_of_unapproved_result = ResultUploadBulk.objects.filter(department__in = chiefadmin.faculty.department_set.all(), status = STATUS.PENDING).count() +\
            ResultUploadSingle.objects.filter(department__in = chiefadmin.faculty.department_set.all(), status = STATUS.PENDING).count()
        
        # latest actions performed by the chief admin
        latest_actions = Action.objects.filter(user = request.user).order_by('-date')[:10]
        context = {
            'chiefadmin': chiefadmin,
            'number_of_department':number_of_department,
            'number_of_courses':number_of_courses,
            'latest_notification':latest_notification,
            'number_of_students':number_of_students,
            'number_of_unapproved_students':number_of_unapproved_students,
            'number_of_admins':number_of_admins,
            'number_of_unapproved_result':number_of_unapproved_result,
            'latest_actions':latest_actions,

        }
        return render(request,"chiefadmin/chiefadmin-home.html", context)



class NotificationListView(ChiefAdminStatus,ListView):
    """
    View for viewing all notification with pagination. inheriting list view fior this.
    url: /chief-admin/notification/
    """
    paginate_by = 30
    template_name = "chiefadmin/chiefadmin-notification.html"
    def get_queryset(self):
        return Notification.objects.filter(user = self.request.user).order_by("-date")

class StudentListView(ChiefAdminStatus, ListView):
    """
    View for viewing all the students in the chief-admin's faculty.
    url: /chief-admin/student/
    """
    template_name = "chiefadmin/chiefadmin-student-list.html"
    paginate_by = 50
    def get_queryset(self):
        return Student.objects.filter(department__in = self.request.usertype.faculty.department_set.all())

    
class StudentDetailView(ChiefAdminStatus, DetailView):
    """
    View for viewing the details of a student in the chief-admin's faculty.
    url: /chief-admin/student/<int:id>/
    """
    model = Student
    template_name = "chiefadmin/chiefadmin-student-detail.html"
    pk_url_kwarg = "id"
    def get_success_url(self):
        obj = self.get_object()
        return reverse("chiefadmin:student_details",{'id':obj.id})
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        student = self.get_object()
        # send the grade list of the student to the context object.
        grade_list = Grade.objects.filter(student = student).values("session").annotate(session_count = Count("session")).order_by("session")
        data['grades'] = grade_list
        return data
    def get(self,request, *args,**kwargs):
        object = self.get_object()
        # Validate if the student belongs to the chief-admin's faculty
        if not request.usertype.validate_student(object):
            return HttpResponseForbidden()
        return super().get( request,*args, **kwargs) 

class CheckResultView(ChiefAdminStatus,View):
    """
    View for viewing a student session and semester result
    url: /chief-admin/student/<id>/<session_id>/<semester>/
    """
    def get(self,request,student_id,session_id,semester):
        student = Student.objects.get(id = student_id)
        # Check if the student is in the chief admin's faculty
        if student.department not in request.usertype.departments():
            return HttpResponseForbidden() # returns 403 error if the student is not
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
        return render(request,"chiefadmin/chiefadmin-student-result", context)

class DownloadResultView(ChiefAdminStatus, View):
    """
    View to download student result to pdf.
    url: /chief-admin/student/<id>/result-download/?session=<int>&semester=<int>
    """
    def get(self,request):
        semester = request.GET.get("semester")
        session_id = request.GET.get("session")
        if not semester or not session_id:
            messages.error(request,"No semester or session specified")
            return HttpResponseBadRequest("Bad Request")
        session = Session.objects.get(id = int(session_id))
        student = Student.objects.get(id = id)
        file = download_result(student, int(semester),session)
        Action.objects.get(user = request.user, message = f"Downloaded {session} {semester} semester" 
                           "of student {student.matric_number} result")
        return FileResponse(file,filename="{student.last_name}-result.pdf")
    

class StudentAddView(ChiefAdminStatus, FormView):
    """
    View for adding a student to a department under the chief admin's faculty.
    url: /chief-admin/student/add/
    """
    form_class = AddStudentForm
    template_name = "chiefadmin/chiefadmin-student-add.html"
    success_url = reverse_lazy("chiefadmin:student_add")
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['chiefadmin'] = self.request.user.chiefadmin
        return kwargs
    def get_context_data(self, **kwargs):

        data = super().get_context_data(**kwargs)
        faculty = self.request.user.chiefadmin.faculty
        departments = Department.objects.filter(faculty = faculty)
        data['departments'] = departments # send valid department list to the context object
        data['form_type'] = "Add" # send form type to the context object
        return data

    def form_valid(self, form):
        obj = form.save(commit = False) # save form temporarily
        obj.approved = True # set student appove to true
        obj.approved_by = self.request.usertype
        user = User()
        user.email = obj.email
        user.save()
        obj.user = user
        obj.save()
        assign_role(user,'student') # assign student role to user.
        messages.success(self.request,"Student Added.")
        Action.objects.create(user = self.request.user,title="Student Add",message = f"Added Student. Matric Number: {obj.matric_number}")
        send_site_mail(user.email,"GradeMe Account","Your Grade Account has been created.\nYour Login Details:"
                       f"Email: {user.email}")
        return super().form_valid(form)

class StudentUpdateView(ChiefAdminStatus, UpdateView):
    """
    View for adding a faculty student's information .
    url: /chief-admin/student/<slug:id>/edit/
    """
    model = Student
    template_name = "chiefadmin/chiefadmin-student-add.html"
    fields = "__all__"
    pk_url_kwarg = "id"
    def get_success_url(self):
        obj = self.get_object()
        return reverse("chiefadmin:student_details",{'id':obj.id})
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        faculty = self.request.usertype.faculty
        departments = Department.objects.filter(faculty = faculty)
        data['departments'] = departments # send valid department list to the context object
        data['form_type'] = "Edit" # send form type to the context object
        return data

    def form_valid(self, form):
        obj = form.save()
        messages.success(self.request,"Student Edited.")
        # Create Edit student Action
        Action.objects.create(user = self.request.user,title="Student Edit",message = f"Edited Student Profile. Matric Number: {obj.matric_number}")
        return super().form_valid(form)

class StudentApprovalView(ChiefAdminStatus,View):
    """
    View for approving a student created by an admin and for creating the student's user instance
    url: /chief-admin/student/<slug:id>/approve/
    """
    def post(self,request,id):
        student = Student.objects.get(id = id)
        if not request.usertype.validate_student(student):
            raise HttpResponseForbidden("Not your faculty!!!")
        if User.objects.filter(email = student.email).exists():
            messages.error(request,"User with this email already exists")
            return redirect(reverse("chiefadmin:student_details",{'id':id}))
        student.approved = True

        # Create User instance for student user
        user = User()
        user.email = student.email
        user.save()
        student.user = user
        student.save()
        assign_role(user,'student') # assign student role to student user instance
        messages.success(self.request,"Student Added.")
        # Create action for the performed action
        Action.objects.create(user = self.request.user,title="Student Add",message = f"Added Student. Matric Number: {student.matric_number}")
        Notification.objects.create(user = student.created_by.user, title="Student Approved",
                                    message = f"The student with matric number {student.matric_number} has been approved and activated"
                                    )
        send_site_mail(user.email,"GradeMe Account","Your Grade Account has been created.\nYour Login Details:"
                       f"Email: {user.email}")
        return redirect(reverse("chiefadmin:student_details",{'id':id}))

class AdminListView(ChiefAdminStatus, ListView):
    """
    View for viewing all the admins in the chief-admin's faculty.
    url: /chief-admin/student/
    """
    template_name = "chiefadmin/chiefadmin-admin-list.html"
    paginate_by = 50
    def get_queryset(self):
        return Admin.objects.filter(department__in = self.request.usertype.departments()).order_by('-date_created')

class AdminAddView(ChiefAdminStatus,FormView):
    """
    View for adding an admin to a department under the chief admin's faculty.
    url: /chief-admin/admin/add/
    """
    form_class = AddAdminForm
    template_name = "chiefadmin/chiefadmin-admin-add.html"
    success_url = reverse_lazy("chiefadmin:admin_add")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['chiefadmin'] = self.request.user.chiefadmin
        return kwargs
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        faculty = self.request.user.chiefadmin.faculty
        departments = Department.objects.filter(faculty = faculty)
        data['departments'] = departments
        data['form_type'] = "Add"
        return data
    def form_valid(self, form):
        obj = form.save(commit = False)
        obj.approved = True
        user = User()
        user.email = obj.email
        user.save()
        obj.user = user
        obj.save()
        assign_role(user,'admin')
        messages.success(self.request,"Admin Added.")
        Action.objects.create(user = self.request.user,title="Admin Add",message = f"Added Admin. Email: {obj.email}")
        send_site_mail(user.email,"GradeMe Account","Your Grade Account has been created.\nYour Login Details:"
                       f"Email: {user.email}")
        self.success_url = reverse("chiefadmin:admin_details",{'id':obj.id})
        return super().form_valid(form)
    
class AdminUpdateView(ChiefAdminStatus, UpdateView):
    """
    View for editing an admin details .
    url: /chief-admin/admin/<slud:id>/edit/
    """
    model = Admin
    template_name = "chiefadmin/chiefadmin-admin-add.html"
    fields = "__all__"
    pk_url_kwarg = "id"
    def get_success_url(self):
        obj = self.get_object()
        return reverse("chiefadmin:student_details",{'id':obj.id})
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        faculty = self.request.usertype.faculty
        departments = Department.objects.filter(faculty = faculty)
        data['departments'] = departments
        data['form_type'] = "Edit"
        return data

    def form_valid(self, form):
        obj = form.save()
        messages.success(self.request,"Admin Edited.")
        Action.objects.create(user = self.request.user,title="Admin Edit",message = f"Edited Admin Profile. email: {obj.email}")
        return super().form_valid(form)

class AdminDetailView(ChiefAdminStatus, DetailView):
    """
    View for viewing an admin details .
    url: /chief-admin/admin/<slud:id>/
    """
    model = Admin
    template_name = "chiefadmin/chiefadmin-admin-detail.html"
    pk_url_kwarg = "id"
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        admin = self.get_object()
        page_num = self.request.GET.get('page',1)
        actions = Action.objects.filter(user = admin.user)
        paginator = Paginator(actions)
        page_obj = paginator.page(page_num)
        data['page_obj'] = page_obj  # sending the admin actions instances to the context in a paginated format
        return data
    def get(self,request, *args,**kwargs):
        object = self.get_object()
        if not request.usertype.validate_admin(object):
            return HttpResponseForbidden()
        return super().get( request,*args, **kwargs)

class DepartmentListView(ChiefAdminStatus, ListView):
    """
    View for viewing all the departments in the chief-admin's faculty.
    url: /chief-admin/department/
    """
    template_name = "chiefadmin/chiefadmin-department-list.html"
    paginate_by = 50
    def get_queryset(self):
        return Department.objects.filter(faculty= self.request.usertype.faculty).order_by('-date_created')

class DepartmentAddView(ChiefAdminStatus, CreateView):
    """
    View for adding a department to the chief admin's faculty.
    url: /chief-admin/department/add/
    """
    model = Department
    fields = "__all__"
    success_url =  reverse_lazy("chiefadmin:department")
    template_name = "chiefadmin/chiefadmin-department-add.html"
    
    def form_valid(self, form):
        messages.success(self.request,"Department Added")
        return super().form_valid(form)
    
class DepartmentUpdateView(ChiefAdminStatus, UpdateView):
    """
    View for updating a department
    url: /chief-admin/department/<int:id>/edit/
    """
    model = Department
    fields = "__all__"
    pk_url_kwarg = "id"
    success_url =  reverse_lazy("chiefadmin:department")
    template_name = "chiefadmin/chiefadmin-department-add.html"
    
    def form_valid(self, form):
        messages.success(self.request,"Department Updated")
        return super().form_valid(form)

class CourseListView(ChiefAdminStatus, ListView):
    """
    View for viewing all the courses being offered in the chief-admin's faculty.
    url: /chief-admin/course/
    """
    template_name = "chiefadmin/chiefadmin-course-list.html"
    paginate_by = 50
    def get_queryset(self):
        return Course.objects.filter(department__in = self.request.usertype.faculty.department_set.all()).order_by('-date_created')
class CourseAddView(ChiefAdminStatus, CreateView):
    """
    View for adding a course to the a department in the faculty. using CreateView by django
    url: /chief-admin/course/add/
    """
    model = Course
    fields = "__all__"
    success_url =  reverse_lazy("chiefadmin:course")
    template_name = "chiefadmin/chiefadmin-course-add.html"
    
    def form_valid(self, form):
        messages.success(self.request,"Course Added")
        return super().form_valid(form)
    
class ApproveSingleResultListView(ChiefAdminStatus,ListView):
    """
    View for viewing all the single results that is yet to be approved in the faculty.
    url: /chief-admin/result/singles/ 
    """
    paginate_by = 50
    template_name = "chiefadmin/chiefadmin-approve-singles.html"
    def get_queryset(self):
        return ResultUploadSingle.objects.filter(department__in = self.request.usertype.departments(), status = STATUS.PENDING).order_by("date_created")
class ApproveSingleResultDetailView(ChiefAdminStatus,DetailView):
    """
    View for a single result details.
    url: /chief-admin/result/singles/<int:id>/
    """
    model = ResultUploadSingle
    template_name = "chiefadmin/chiefadmin-approve-single-view.html"
    pk_url_kwarg = "id"
    def get(self,request, *args,**kwargs):
        object = self.get_object()
        # Prevent chief admin from viewing another faculty's result 
        if not request.usertype.validate_department(object.department):
            return HttpResponseForbidden()
        return super().get( request,*args, **kwargs)
    
class ApproveBulkResultListView(ChiefAdminStatus,ListView):
    """
    View for viewing all the bulk results that is yet to be approved in the faculty.
    url: /chief-admin/result/bulk/ 
    """
    paginate_by = 50
    template_name = "chiefadmin/chiefadmin-approve-bulk.html"
    def get_queryset(self):
        return ResultUploadBulk.objects.filter(department__in = self.request.usertype.departments(), status = STATUS.PENDING).order_by("date_created")
class ApproveBulkResultDetailView(ChiefAdminStatus,DetailView):
    """
    View for a bulk result details.
    url: /chief-admin/result/singles/<int:id>/
    """
    model = ResultUploadBulk
    template_name = "chiefadmin/chiefadmin-approve-bulk-view.html"
    pk_url_kwarg = "id"
    def get(self,request, *args,**kwargs):
        object = self.get_object()
        # Prevent chief admin from viewing another faculty's result 
        if not request.usertype.validate_department(object.department):
            return HttpResponseForbidden()
        return super().get( request,*args, **kwargs)
class ApprovalResultHistoryView(ChiefAdminStatus,ListView):
    """
    View for viewing all the approved result. both bulk and single.
    url: /chief-admin/result/history/ 
    """
    template_name = "chiefadmin/chiefadmin-approval-history.html"
    paginate_by = 50
    def get_queryset(self):
        admin = self.request.usertype
        qs_list = [*ResultUploadBulk.objects.filter(department__in= admin.departments()).exclude(status = STATUS.PENDING).annotate(type="bulk"),
                   *ResultUploadSingle.objects.filter(department__in= admin.departmnts()).exclude(status = STATUS.PENDING).annotate(type="single")]
        qs_list.sort(key=lambda x: x.date_created, reverse=True)
        return qs_list 

class ApproveorRejectSingleResultView(ChiefAdminStatus,View):
    """
    View for approving a single result.
    url: /chief-admin/result/singles/<int:id>/approve/
    """
    def post(self,request,result_id,status):
        result= ResultUploadSingle.objects.get(id = result_id)
        if result.department not in request.usertype.departments(): # Prevent chief admin from assessing another faculty's result
            return HttpResponseForbidden("Not Allowed")
        if result.status != STATUS.PENDING: # prevent chief admin from trying to approve or reject the result again
            messages.error(request,"Result already approved or rejected")
            return redirect(reverse("chiefadmin:approve_single_result"))
        if status == STATUS.APPROVED: # check whether it is an approve request 

            # Check if the grade already exists. if it does, replace the grade else create the grade.
            grade, created = Grade.objects.get_or_create(student = result.student,course = result.course,session = result.session,
                                                semester = result.semester)
            grade.score = result.score
            grade.grade = result.grade
            grade.uploaded_by = result.uploaded_by
            grade.approved_by = request.usertype
            grade.save()
            result.status = STATUS.APPROVED
            result.approved_by = self.request.usertype
            result.save()
             # send notification message to admin that uploaded the result
            Notification.objects.create(user = result.uploaded_by.user,title = "Result Approved",
                                        message=f"The result of student ({result.student.matric_number}) for {result.course} has been approved")
             # create action for approval
            Action.objects.create(user = request.user, title="Result Approval",
                                  message=f"The result of student ({result.student.matric_number}) for {result.course} has been approved by you")
            messages.success(request,"Result Approved")
            return redirect(reverse("chiefadmin:approve_single_result"))
        elif status == STATUS.REJECTED: # Check whether it is a reject request 
            result.status = STATUS.REJECTED
            result.approved_by = self.request.usertype
            result.save()
             # send notification message to admin that uploaded the result
            Notification.objects.create(user = result.uploaded_by.user,title = "Result Rejected",
                                        message=f"The result of student ({result.student.matric_number}) for {result.course} has been rejected")
             # create action for rejection
            Action.objects.create(user = request.user, title="Result Rejected",
                                  message=f"The result of student ({result.student.matric_number}) for {result.course} has been rejected by you")
            messages.success(request,"Result Rejected")
            return redirect(reverse("chiefadmin:approve_single_result"))
        
        return HttpResponseBadRequest("Unknown Request")


class ApproveorRejectBulkResultView(ChiefAdminStatus,View):
    """
    View for approving a bulk result.
    url: /chief-admin/result/bulk/<int:id>/approve/
    """
    def post(self,request,result_id,status):
        result= ResultUploadBulk.objects.get(id = result_id)
        if result.department not in request.usertype.departments():  # Prevent chief admin from assessing another faculty's result
            return HttpResponseForbidden("Not Allowed")
        if result.status != STATUS.PENDING: # prevent chief admin from trying to approve or reject the result again
            messages.error(request,"Result already approved or rejected")
            return redirect(reverse("chiefadmin:approve_bulk_result"))
        
        if status == STATUS.APPROVED:  # check whether it is an approve request 
            file_type = result.file.name.rsplit('.',maxsplit=2)[-1].lower() 
            if file_type not in settings.VALID_RESULT_FILE_EXTENSION:
                messages.error(request,"Invalid File Type")
                return redirect(reverse("chiefadmin:approve_bulk_result"))
            result.status = STATUS.APPROVED
            result.approved_by = self.request.usertype
            result.save()
            upload_approved_result_bulk.delay(result.id) # Create grades in background using celery
            messages.success(request,"Grade Uploading... you will be notified when all the grades has been uploaded")
        elif status == STATUS.REJECTED:  # check whether it is a reject request 
            result.status = STATUS.REJECTED
            result.approved_by = self.request.usertype
            result.save()

            # send notification message to admin that uploaded the result
            Notification.objects.create(user = result.uploaded_by.user,title = "Result Rejected",
                                        message=f"The bulk result of {result.course} for {result.session} Semester {result.semester} has been rejected")
            # create action for rejection
            Action.objects.create(user = request.user, title="Result Rejected",
                                  message=f"The result of student ({result.student.matric_number}) for {result.course} has been rejected by you")
            messages.success(request,"Result Rejected")
            return redirect(reverse("chiefadmin:approve_single_result"))
        return HttpResponseBadRequest("Unknown Request")