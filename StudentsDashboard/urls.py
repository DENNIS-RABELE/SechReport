from django.urls import path
from . import views

urlpatterns = [
    path('', views.submit_report, name='submit_report'),
    path('track/', views.track_report, name='track_report'),
    path('conversation/<str:token>/', views.conversation, name='conversation'),
]