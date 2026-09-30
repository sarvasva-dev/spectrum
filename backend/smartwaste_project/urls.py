"""
Root URL Configuration for smartwaste_project.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

# Custom HTTP error handlers
handler404 = 'waste_management.views.custom_404_view'
handler500 = 'waste_management.views.custom_500_view'
handler403 = 'waste_management.views.custom_403_view'

urlpatterns = [
    # Default Django Superuser Admin
    path('admin/', admin.site.urls),

    # Main Waste Management Application
    path('', include('waste_management.urls')),
    
    # SEO
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('sitemap.xml', TemplateView.as_view(template_name="sitemap.xml", content_type="application/xml")),
]

# In development or fallback, serve uploaded media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
