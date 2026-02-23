from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('report/<int:report_id>/login/', views.report_login_gate, name='report_login_gate'),
    path('report/<int:report_id>/', views.report_detail, name='report_detail'),
]
