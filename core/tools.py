import csv
from typing import Dict, List,Optional
import xlwings as xw
import io
import secrets

from django.conf import settings
from django.template.loader import render_to_string
from django.http.response import FileResponse
from django.db.models import Sum,F
from django.core.mail import send_mail

from .models import Grade
class FileConverter:
    """
    Abstract Class for the file converter classes
    """
    def headers(self):
        """
        Returns the headers of the file. at the first row
        """
        raise NotImplementedError
    def convert_to_dictlist(self,allowed_headers=None):
        raise NotImplementedError

class CSVConverter(FileConverter):
    """
    Class for Converting csv files to python objects
    """
    def __init__(self, filename:str):
        self.filename = filename
        self.formats = ['csv']

    def full_read(self):
        """
        Returns the csv reader instance
        """
        with open(self.filename) as file:
            csvreader = csv.DictReader(file)
        return csvreader



    def convert_to_dictlist(self,allowed_headers:Optional[List[str]]=None):
        """
        Converts the rows in a csv file to a list of dict
        """
        dictlist = []
        with open(self.filename) as file:
            csvreader = csv.DictReader(file)
            fieldnames = csvreader.fieldnames
            fieldnames = list(map(lambda x: x.lower(), fieldnames))
            
            if allowed_headers and type(allowed_headers) == list and len(allowed_headers) > 0:
                allowed_headers = list(map(lambda x: x.lower(), allowed_headers))
                fieldnames = list(filter(lambda x: x in allowed_headers,fieldnames))
            for row in csvreader:
                maindict = {}
                for x in fieldnames:
                    maindict[x] = row[x]
                dictlist.append(maindict)
        
        return dictlist
    def headers(self):
        """
        Return the headers of the csv file.
        """
        fieldnames = []
        with open(self.filename) as file:
            csvreader = csv.DictReader(file)
            fieldnames = csvreader.fieldnames
        return fieldnames
    def check_format(self):
        filename = self.filename
        filnamesplit = filename.rsplit(".",2)
        if filnamesplit[-1].lower() not in self.formats:
            return False
        return True

class ExcelConverter(FileConverter):
    """
    Class for Converting excel files to python objects
    """
    def __init__(self, filename:str, read_only=True):
        self.filename = filename
        self.formats = ['xlsx','xlsm','xltx''xltm']
        if not self.check_format():
            raise TypeError("Invalid File Type")
        # create the workbook instance
        self.workbook = xw.Book(self.filename, read_only=read_only)

        # select the main sheet i.e the first sheet
        self.mainexcelsheet = self.workbook.sheets[0]

    def full_read(self):
        """
        Returns the csv reader instance
        """
        fullcontent = self.mainexcelsheet.range("A1").expand().value
        return fullcontent

    def convert_to_dictlist(self,allowed_headers:Optional[List[str]]=None):
        """
        Converts the rows in an excel file to a list of dict
        """
        dictlist = []
        content = self.mainexcelsheet.range("A1").expand().value
        headers = content[0]
        bodycontent = content[1:]
        for row in bodycontent:
            maindict = {}
            for idx, col in enumerate(headers):
                try:
                    maindict[col] = row[idx]
                except Exception:
                    maindict[col] = ""
            dictlist.append(maindict)
        return dictlist
                


        
        
        return dictlist
    def headers(self):
        """
        Return the headers of the excel file.
        """
        content = self.mainexcelsheet.range("A1").expand().value
        return content[0]
    def check_format(self):
        filename = self.filename
        filnamesplit = filename.rsplit(".",2)
        if filnamesplit[-1].lower() not in self.formats:
            return False
        return True
    
def calculate_gpa(student_grades):
    grades = student_grades.annotate(point = F('course__unit_load') * F('grade')).\
                aggregate(total_point = Sum('poin'),total_unit = Sum('course__unit_load'))
    return grades['total_point'] / grades['total_unit']  

def download_result(student,semester,session):
    """
    Returns the result of the student compiled into a pdf
    """
    import weasyprint
    grades = Grade.objects.filter(student= student, semester=semester, session=session)
    template = "grade-download-template.html"
    gpa = calculate_gpa(grades)
    html = render_to_string(template, {
        'grades': grades,
        'student': student,
        'semester': semester,
        'session': session,
        'gpa': grades
    })
    buffer = io.BytesIO()
    weasyprint.HTML(string=html).write_pdf(buffer,
        stylesheets=[weasyprint.CSS(settings.STATIC_ROOT / "css/pdf.css")])
    buffer.seek(0)
    return buffer

def generate_code(code_length = 6):
    """
    Generate a code of length :params: code_length
    """
    import random
    start = int("1"+"0"*(code_length - 1))
    end = int("9"*code_length)

    return random.randint(start, end)

def send_login_code(email,code):
        email_address = email
        message = f"""
A login request has been made to your grademe account. contact support if it is not you.
Verification Code : {code}
"""
        send_mail("GradeMe Login",message,"support@grademe.com",[email_address], fail_silently=True)

def send_code(email, code, title, message):
    email_address = email
    message = f"""
    {message}
Verification Code : {code}
"""
    send_mail(title,message,"support@grademe.com",[email_address], fail_silently=False)

def send_site_mail(email,subject,message,fail_silently = True):
    sender_email = "admin@grademe.com"
    send_mail(subject,message,sender_email,[email],fail_silently)

def generate_password():
    return secrets.token_urlsafe(8)


def get_device_info():
    pass
def get_location_info():
    pass
# if __name__ == "__main__":
#     excel = ExcelConverter("products.xlsx")
#     print(excel.convert_to_dictlist())