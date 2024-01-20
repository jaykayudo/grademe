from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect
from django.http import HttpResponseForbidden,Http404

class ChiefAdminStatus(LoginRequiredMixin,UserPassesTestMixin):
    """
    Class Mixin to check whether user has chief admin status
    """
    login_url = reverse_lazy('chiefadmin_login')
    def test_func(self):
        return self.request.user.is_chief_admin

class AdminStatus(LoginRequiredMixin,UserPassesTestMixin):
    """
    Class Mixin to check whether user has admin status
    """
    login_url = reverse_lazy('admin_login')
    def test_func(self):
        return self.request.user.is_admin

class StudentStatus(LoginRequiredMixin,UserPassesTestMixin):
    """
    Class Mixin to check whether user has student status
    """
    login_url = reverse_lazy('student_login')
    def test_func(self):
        return self.request.user.is_student



def chief_admin_status(func):
    """
    Decorator to check whether user has chief admin status
    """
    login_url = reverse('chiefadmin_login')
    def innerfunc(*args,**kwargs):
        request = kwargs['request']
        if not request.user.is_authenticated:
            return redirect(login_url)
        if not request.user.is_chief_admin:
            return HttpResponseForbidden(content="Not allowed for non-chiefadmin")
        return func(*args,**kwargs)
    return innerfunc
def admin_status(func):
    """
    Decorator to check whether user has admin status
    """
    login_url = reverse('admin_login')
    def innerfunc(*args,**kwargs):
        request = kwargs['request']
        if not request.user.is_authenticated:
            return redirect(login_url)
        if not request.user.is_admin:
            return HttpResponseForbidden(content="Not allowed for non-admin")
        return func(*args,**kwargs)
    return innerfunc
def student_status(func):
    """
    Decorator to check whether user has student status
    """
    login_url = reverse('student_login')
    def innerfunc(*args,**kwargs):
        request = kwargs['request']
        if not request.user.is_authenticated:
            return redirect(login_url)
        if not request.user.is_student:
            return HttpResponseForbidden(content="Not allowed for non-students")
        return func(*args,**kwargs)
    return innerfunc

