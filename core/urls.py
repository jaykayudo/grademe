from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('',views.landing_view),
    path('change-email/verify-current-email/',views.CurrentEmail.as_view(),name='current_email_verify'),
    path('change-email/verify-current-email-code/',views.ConfirmCurrentEmail.as_view(),name='current_email_verify_code'),
    path('change-email/verify-new-email/',views.NewEmail.as_view(),name='new_email_verify'),
    path('change-email/verify-new-email-code/',views.NewEmail.as_view(),name='new_email_verify_code'),
]