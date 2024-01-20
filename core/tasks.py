from celery import shared_task
from collections import Counter

from django.core.mail import send_mail

from .models import  Notification, Grade, ResultUploadBulk, Student, GRADE
from .tools import ExcelConverter, CSVConverter

@shared_task
def upload_approved_result_bulk(result_id,file_type="csv"):
    """
    Task to create the grade object for student grades in the background.
    It will take time for a lot of students so it is better to run it in the background.

    The headers should be Matric Number, Grade, Score.
    This is what should be uploaded
    """
    result = ResultUploadBulk(id = result_id)

    if file_type == "csv":
        converter = CSVConverter(result.file.path)
    else:
        converter = ExcelConverter(result.file.path)
    dictlist = converter.convert_to_dictlist()
    counter = Counter()
    bad_rows = []
    
    admin = result.uploaded_by
    chiefadmin = result.approved_by
    for resultdict in enumerate(dictlist):
        try:
            student = Student.objects.get(matric_number = resultdict['matric number'])
            score = int(resultdict['score'])
            grade = GRADE[resultdict['grade'].upper()]
            grade = Grade.objects.get_or_create(student = student, semester = result.semester, session = result.session
                                                , course= result.course)[0]
            grade.grade = grade
            grade.score = score
            grade.uploaded_by = admin
            grade.approved_by = chiefadmin
            grade.save()
            Notification.objects.create(user = student.user, title="Result Upload", message = f"Your {result.course} has been uploaded.")
            counter['good_row'] += 1
 
        except Exception:
            bad_rows.append(result)

    Notification.objects.create(user = admin.user, title="Result Approval", message = f"""
    The bulk uploaded result of {result.course} has been approved. Number of Bad result: {len(bad_rows)}.
    Number of Good Result: {counter['good_row']}. Contact the Chief Administrator for more info.
""")
    Notification.objects.create(user = chiefadmin.user,title="Results Uploaded", message=f"""
     The bulk result of {result.course} has been uploaded. Number of Bad result: {len(bad_rows)}.
    Number of Good Result: {counter['good_row']}.  Bad results: {str(bad_rows)}.
""")
        
    