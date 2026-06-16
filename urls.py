"""
URL configuration for Latina Dance Academy project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
import os
import views


urlpatterns = [
    # Admin (not translated)
    path('admin/', admin.site.urls),
    
    # Language selection
    path('i18n/', include('django.conf.urls.i18n')),
]

# Add static and media URLs in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve media files using the web server (e.g., Nginx, Apache)
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
        path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
    ]

# Translatable URLs
urlpatterns += i18n_patterns(
    # Main pages (using Django views)
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('courses/', views.courses, name='courses'),
    path('gallery/', include('gallery.urls')),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/progress/', views.update_progress, name='update_progress'),
    path('debug/video/<int:session_id>/', views.debug_video, name='debug_video'),
    path('course/<int:course_id>/progress/', views.get_user_progress, name='get_user_progress'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    
    # Programs (Explore Programs feature)
    path('explore-programs/', include('programs.urls')),
    
    # Pricing (Subscription system)
    path('pricing/', include('pricing.urls')),
    
    # Django app URLs
    path('api/courses/', include('courses.urls')),
    path('api/newsletter/', include('newsletter.urls', namespace='newsletter_api')),
    path('api/users/', include('users.urls', namespace='users_api')),
    path('api/', include('payments.urls')),  # Payments API endpoints
    
    # User authentication and dashboard
    path('', include('users.urls')),
    
    # Newsletter URLs (direct access)
    path('newsletter/', include('newsletter.urls')),
    
    # Slideshow API
    path('api/slideshow/', include('slideshow.urls')),
    
    prefix_default_language=False,
)

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
