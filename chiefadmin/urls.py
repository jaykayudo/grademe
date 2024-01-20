from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'chiefadmin'

urlpatterns = [
    path('login/', views.ChiefAdminLoginView.as_view(),name="login"),
    path('login/verify/', views.ChiefAdminLoginConfirmView.as_view(),name="login_verify"),
    path('login/verify/resend-code/', views.resend_login_code,name="resend_code"),
    path('logout/', views.logout_user,name="logout"),
    path('change-email/', TemplateView.as_view(template_name = "chiefadmin/chiefadmin-change-email.html"),name="change_email"),
    path('change-password/', views.ChangePassword.as_view(),name="change_password"),
    path('profile/', views.ProfileView.as_view(),name="profile"),
    path('dashboard/', views.DashboardView.as_view(),name="dashboard"),
    path('notification/', views.NotificationListView.as_view(),name="notification"),

    path('student/', views.StudentListView.as_view(),name="student"),
    path('student/add/', views.StudentAddView.as_view(),name="student_add"),
    path('student/<slug:id>/', views.StudentDetailView.as_view(),name="student_details"),
    path('student/<slug:id>/', views.StudentUpdateView.as_view(),name="student_edit"),
    path('student/<slug:id>/approve/', views.StudentApprovalView.as_view(),name="student_approve"),
    path('student/<slug:id>/<int:session_id>/<int:semester>/', views.CheckResultView.as_view(),name="student_result"),
    path('student/<slug:id>/result-download/',views.DownloadResultView.as_view(),name='student_result_download'),
    path('admin/',views.AdminListView.as_view(),name='admin'),
    path('admin/add/',views.AdminAddView.as_view(),name='admin_add'),
    path('admin/<slug:id>/',views.AdminDetailView.as_view(),name='admin_details'),
    path('admin/<slug:id>/edit/',views.AdminUpdateView.as_view(),name='admin_edit'),
    path('department/',views.DepartmentListView.as_view(),name='department'),
    path('department/add/',views.DepartmentAddView.as_view(),name='department_add'),
    path('department/<slug:id>/edit/',views.DepartmentUpdateView.as_view(),name='department_edit'),
    path('course/',views.CourseListView.as_view(),name='course'),
    path('course/add/',views.CourseAddView.as_view(),name='course_add'),
    path('result/single/',views.ApproveSingleResultListView.as_view(),name='result_single'),
    path('result/single/<int:id>/',views.ApproveSingleResultDetailView.as_view(),name='result_single_details'),
    path('result/single/<int:id>/<int:status>/',views.ApproveorRejectSingleResultView.as_view(),name='result_single_status_change'),
    path('result/bulk/',views.ApproveBulkResultListView.as_view(),name='result_bulk'),
    path('result/bulk/<int:id>/', views.ApproveBulkResultDetailView.as_view(),name="result_bulk_details"),
    path('result/bulk/<int:id>/<int:status>/', views.ApproveorRejectBulkResultView.as_view(),name="result_bulk_status_change"),
    path('result/history/', views.ApprovalResultHistoryView.as_view(),name="result_history"),

]