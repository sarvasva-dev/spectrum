"""
URL Configuration for waste_management app.
Maps web endpoints to view functions with clear, readable route names.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Public Pages

    path('man-of-the-month/', views.man_of_the_month_view, name='man_of_the_month'),
    path('man-of-the-month/<slug:slug>/', views.man_of_the_month_view, name='man_of_the_month_slug'),
    path('', views.landing_view, name='landing'),
    path('guide/', views.guide_view, name='guide'),
    path('awareness/', views.waste_awareness_view, name='awareness'),
    path('robots.txt', views.robots_txt_view, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml_view, name='sitemap_xml'),

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

    # API Playground & REST Endpoints
    path('visual/', views.api_playground_view, name='api_playground'),
    path('ai/', views.ai_view, name='ai'),
    path('api/ai/chat/', views.api_ai_chat_view, name='api_ai_chat'),
    path('api/health/', views.api_health_view, name='api_health'),
    path('api/complaints/', views.api_complaint_list_create_view, name='api_complaint_list_create'),
    path('api/complaints/<str:complaint_id>/', views.api_complaint_detail_update_delete_view, name='api_complaint_detail_update_delete'),
]
