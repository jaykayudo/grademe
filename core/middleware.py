from rolepermissions.checkers import has_role
from .models import Student, Admin, ChiefAdmin
class UserTypeMiddleware:
    """
    Middleware to set where type of user a user is.
    Whether admin or student or chiefadmin
    """
    def __init__(self, get_response):
        self.get_response = get_response
        

    def __call__(self, request):
        user = request.user
        if has_role(user,'student'):
            request.usertype = Student.objects.get(user = user)
        elif has_role(user,'admin'):
            request.usertype = Admin.objects.get(user = user)
        elif has_role(user,'chief_admin'):
            request.usertype = ChiefAdmin.objects.get(user = user)
        else:
            request.usertype = None
        response = self.get_response(request)
        return response