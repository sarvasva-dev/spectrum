"""
URL Configuration for waste_management app.
Maps web endpoints to view functions with clear, readable route names.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Public Pages
    path('', views.landing_view, name='landing'),
    path('awareness/', views.waste_awareness_view, name='awareness'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Citizen Dashboard & Actions
    path('dashboard/', views.citizen_dashboard_view, name='citizen_dashboard'),
    path('report/', views.report_waste_view, name='report_waste'),
    path('tracking/', views.complaint_tracking_view, name='complaint_tracking'),
    path('complaint/<str:complaint_id>/', views.complaint_detail_view, name='complaint_detail'),
    path('pickup/', views.pickup_request_view, name='pickup_request'),
    path('pickup/list/', views.pickup_list_view, name='pickup_list'),

    # Municipal Admin Portal & Actions
    path('admin-portal/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-portal/complaint/<str:complaint_id>/', views.admin_complaint_update_view, name='admin_complaint_update'),
    path('admin-portal/pickup/<str:pickup_id>/', views.admin_pickup_update_view, name='admin_pickup_update'),
]
