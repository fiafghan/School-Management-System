from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Student management
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    
    # Payment management
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_add, name='payment_add'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # API endpoints
    path('api/students/<int:student_id>/payments/', views.api_student_payments, name='api_student_payments'),
    path('api/reports/data/', views.api_report_data, name='api_report_data'),
]
