from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'normaladmin'

urlpatterns = [
    path('login/', views.AdminLoginView.as_view(),name="login"),
    path('login/verify/', views.AdminLoginConfirmView.as_view(),name="login_verify"),
    path('login/verify/resend-code/', views.resend_login_code,name="resend_code"),
    path('logout/', views.logout_user,name="logout"),
    path('change-email/', TemplateView.as_view(template_name = "normaladmin/admin-change-email.html"),name="change_email"),
    path('change-password/', views.ChangePassword.as_view(),name="change_password"),
    path('profile/', views.ProfileView.as_view(),name="profile"),
    path('dashboard/', views.DashboardView.as_view(),name="dashboard"),
    path('notification/', views.NotificationListView.as_view(),name="notification"),
    path('messages/grade-report/', views.GradeReportListView.as_view(),name="grade_report"),
    path('messages/grade-report/<int:id>/', views.GradeReportDetailView.as_view(),name="grade_report_details"),
    path('messages/support-messages/', views.SupportListView.as_view(),name="support_messages"),
    path('messages/support-messages/<int:id>/', views.SupportDetailView.as_view(),name="support_messages_details"),
   
    path('student/', views.StudentListView.as_view(),name="student"),
    path('student/<slug:id>/', views.StudentDetailView.as_view(),name="student_details"),
    path('student/add/', views.StudentAddView.as_view(),name="student_add"),
    path('student/<int:id>/<int:session_id>/<int:semester>/', views.CheckResultView.as_view(),name="student_result"),
    path('student/<id>/result-download/',views.DownloadResultView.as_view(),name='student_result_download'),
    path('result/upload-bulk/',views.ResultUploadBulkView.as_view(),name='upload_bulk'),
    path('result/upload-single/',views.ResultUploadSingleView.as_view(),name='upload_single'),
    path('result/upload-history/', views.UploadHistoryListView.as_view(),name="upload_history"),

]