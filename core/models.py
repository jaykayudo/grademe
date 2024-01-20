import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.db.models import F, Count, Avg, Sum
from rolepermissions.checkers import has_role



class SEMESTER(models.TextChoices):
    FIRST = 1,"first semester"
    SECOND = 2,"second semester"

class GRADE(models.TextChoices):
    A = 5,"A"
    B = 4,"B"
    C = 3,"C"
    D = 2,"D"
    E = 1,"E"
    F = 0,"F"

class STATUS(models.TextChoices):
    APPROVED = 2, "approved"
    REJECTED = 3, "rejected"
    PENDING = 1, "pending"


# Create your models here.
class UserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self,email,password,**extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_user(self,email,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',False)
        extra_fields.setdefault('is_superuser',False)
        return self._create_user(email,password,**extra_fields)
    def create_superuser(self,email,password,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        return self._create_user(email,password,**extra_fields)

class User(AbstractUser):
    """
    User Model
    """
    username = None
    email = models.EmailField('email address',unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    @classmethod
    def get_deleted_user(cls):
        return cls.objects.get_or_create(email = "deleteduser@grademe.com")[0]
    @property
    def is_admin(self):
        return has_role(self,'admin')
    @property
    def is_student(self):
        return has_role(self,'student')
    @property
    def is_chief_admin(self):
        return has_role(self,'chief_admin')

class Faculty(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Session(models.Model):
    name = models.CharField(max_length = 10 )
    start_year = models.IntegerField(null = True, blank = True)
    end_year = models.IntegerField(null = True, blank=True)
    current = models.BooleanField(default = False)

    def __str__(self):
        return self.name


class Department(models.Model):
    faculty = models.ForeignKey(Faculty,on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey('ChiefAdmin', null = True, blank = True, on_delete = models.SET_NULL)
    date_created = models.DateField(auto_now_add = True)

    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length = 100)
    code = models.CharField(max_length=10)
    department = models.ForeignKey(Department,on_delete = models.CASCADE)
    unit_load = models.PositiveIntegerField()
    semester = models.PositiveIntegerField(choices=SEMESTER.choices)
    created_by = models.ForeignKey('ChiefAdmin', null = True, blank = True, on_delete = models.SET_NULL)
    date_created = models.DateField(auto_now_add = True)

    def __str__(self):
        return self.code


class Student(models.Model):
    id  = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="student-profile-image")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phonenumber = models.CharField(max_length=13, blank=True, null=True)
    matric_number = models.CharField(max_length=20,unique = True)
    email = models.EmailField(unique = True)
    department = models.ForeignKey(Department,on_delete=models.PROTECT)
    approved = models.BooleanField(default=False)
    created_by = models.ForeignKey('Admin',null=True,blank=True, on_delete = models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add = True)
    date_approved = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.matric_number} - {self.first_name} {self.last_name}"
    
    def calculate_cgpa(self):
        if self.grade_set.exists():
            grade = Grade.objects.filter(student = self).annotate(point = F('course__unit_load') * F('grade')).\
                aggregate(total_point = Sum('poin'),total_unit = Sum('course__unit_load'))
            return grade['total_point']/grade['total_unit']
        else:
            return f'5.0 (no record yet)'

    

class Admin(models.Model):
    id  = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="admin-profile-image")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phonenumber = models.CharField(max_length=13, blank=True, null=True)
    department = models.ForeignKey(Department,on_delete=models.PROTECT)
    temp_pass = models.BooleanField(default = True)
    created_by = models.ForeignKey('ChiefAdmin', on_delete = models.DO_NOTHING)
    date_created = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class ChiefAdmin(models.Model):
    id  = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User,blank=True, null=True, on_delete = models.CASCADE)
    image = models.ImageField(upload_to="chiefadmin-profile-image")
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phonenumber = models.CharField(max_length=13, blank=True, null=True)
    faculty = models.ForeignKey(Faculty,on_delete=models.PROTECT)
    temp_pass = models.BooleanField(default = True)
    date_created = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def validate_student(self,student):
        return student.department in self.departments
    def validate_admin(self,admin):
        return admin.department in self.departments
    def validate_department(self,department):
        return department in self.departments
    def departments(self):
        departments = Department.objects.filter(faculty = self.faculty)
        return departments

class Grade(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete= models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.PROTECT)
    semester = models.IntegerField(choices=SEMESTER.choices)
    grade = models.PositiveSmallIntegerField(choices=GRADE.choices)
    score = models.PositiveIntegerField(validators = [MaxValueValidator(100), MinValueValidator(0)])
    uploaded_by = models.ForeignKey(Admin,null = True, on_delete=models.SET_NULL)
    approved_by = models.ForeignKey(ChiefAdmin, null=True, on_delete = models.CASCADE)
    date_created = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'{self.student} - {self.grade} - {self.course}'
    @property
    def point(self):
        return self.grade * self.course.unit_load
    

    
class GradeReport(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete = models.CASCADE)
    message = models.TextField()
    reply = models.TextField(blank = True, null=True)
    date_created = models.DateTimeField(auto_now_add = True)


    def __str__(self):
        return self.message

class ResultUploadSingle(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete= models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.PROTECT)
    semester = models.IntegerField(choices=SEMESTER.choices)
    department = models.ForeignKey(Department, on_delete = models.PROTECT)
    grade = models.PositiveSmallIntegerField(choices=GRADE.choices)
    score = models.PositiveIntegerField(validators = [MaxValueValidator(100), MinValueValidator(0)])
    status = models.PositiveIntegerField(choices = STATUS.choices, default = STATUS.PENDING)
    uploaded_by = models.ForeignKey(Admin,null = True,blank=True, on_delete=models.SET_NULL)
    approved_by = models.ForeignKey(ChiefAdmin, blank=True,null=True, on_delete = models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add = True)
    date_updated = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'{self.student} - {self.grade} - {self.course}'
    def get_absolute_url(self):
        return reverse("result-single-view",kwargs={"id":self.id})

class ResultUploadBulk(models.Model):
    course = models.ForeignKey(Course, on_delete= models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.PROTECT)
    semester = models.IntegerField(choices=SEMESTER.choices)
    department = models.ForeignKey(Department, on_delete = models.PROTECT)
    file = models.FileField(upload_to="result-files")
    status = models.PositiveIntegerField(choices = STATUS.choices, default = STATUS.PENDING)
    uploaded_by = models.ForeignKey(Admin,null = True,blank=True, on_delete=models.SET_NULL)
    approved_by = models.ForeignKey(ChiefAdmin, blank=True,null=True, on_delete = models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add = True)
    date_updated = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'{self.session} - {self.course}'
    
    def get_absolute_url(self):
        return reverse("result-bulk-view",kwargs={"id":self.id})
    
class SupportMessage(models.Model):
    student = models.ForeignKey(Student, on_delete = models.CASCADE)
    department = models.ForeignKey(Department, null = True, on_delete = models.SET_NULL)
    title = models.CharField(max_length = 50)
    message = models.CharField(max_length = 100)
    date = models.DateTimeField(auto_now_add=True)
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    title = models.CharField(max_length = 50)
    message = models.CharField(max_length = 100)
    date = models.DateTimeField(auto_now_add=True)

class Action(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    title = models.CharField(max_length = 50)
    message = models.CharField(max_length = 100)
    date = models.DateTimeField(auto_now_add=True)

