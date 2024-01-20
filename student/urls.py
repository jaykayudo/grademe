from django.urls import path
from django.views.generic import TemplateView

from . import views


app_name = "student"
urlpatterns = [
    path('login/', views.StudentLoginView.as_view(),name="login"),
    path('login/verify/', views.StudentLoginVerifyView.as_view(),name="login_verify"),
    path('login/verify/resend-code/', views.resend_login_code,name="resend_code"),
    path('logout/', views.logout_user,name="logout"),
    path('change-email/', TemplateView.as_view(template_name = "student/student-change-email.html"),name="change_email"),
    path('profile/', views.ProfileView.as_view(),name="profile"),
    path('dashboard/', views.DashboardView.as_view(),name="dashboard"),
    path('notification/', views.NotificationListView.as_view(),name="notification"),
    path('check-result/',views.CheckResultView.as_view(), name="check_result"),
    path('check-result/download/',views.DownloadResultView.as_view(), name="check_result_download"),
    path('check-result/report/<int:grade_id>/',views.GradeReportView.as_view(), name="grade_report"),
    path('support/',views.SupportMessageView.as_view(), name="support"),
]