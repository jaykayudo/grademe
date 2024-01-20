from rolepermissions.roles import AbstractUserRole
class Student(AbstractUserRole):
    available_permissions = {
        'check_result': True,
        'login_student_portal': True
    }

class Admin(AbstractUserRole):
    available_permissions = {
        'upload_result': True,
        'add_student':True,
        'login_admin_portal':True
    }

class ChiefAdmin(AbstractUserRole):
    available_permissions = {
        'approve_result':True,
        'add_student':True,
        'edit_student':True,
        'add_department':True,
        'add_course':True
    }