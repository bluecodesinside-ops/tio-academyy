"""
URL configuration for Latina Dance Academy project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
import views
from payments import views as payment_views
from users import views as user_views


urlpatterns = [
    # Admin (not translated)
    path('admin/', admin.site.urls),
    
    # Language selection
    path('i18n/', include('django.conf.urls.i18n')),
    # Stripe webhooks must stay outside i18n — Stripe posts to a fixed URL.
    path('watch/<int:session_id>/', views.watch_session, name='watch_session_root'),
    path('payments/webhook/', payment_views.stripe_webhook, name='stripe_webhook_root'),
    path('api/webhook/', payment_views.stripe_webhook, name='stripe_webhook_unprefixed'),
    path('api/stripe/webhook/', payment_views.stripe_webhook, name='stripe_webhook_api_unprefixed'),
    # Visit counter — outside i18n so every page hits one stable URL.
    path('stats/hit/', user_views.stats_hit, name='stats_hit'),
]

# Static/media via Django only in development.
# In production Nginx serves /static/ and /media/ (do not use django.views.static.serve).
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Translatable URLs
_i18n_patterns = [
    # Main pages (using Django views)
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('courses/', views.courses, name='courses'),
    path('gallery/', include('gallery.urls')),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/packet/<int:packet_id>/', views.packet_detail, name='packet_detail'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('watch/<int:session_id>/', views.watch_session, name='watch_session'),
    path('session/<int:session_id>/progress/', views.update_progress, name='update_progress'),
    path('course/<int:course_id>/progress/', views.get_user_progress, name='get_user_progress'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    
    # Legacy Explore Programs → redirects to /courses/ (see programs.urls)
    path('explore-programs/', include('programs.urls')),
    
    # Pricing (Subscription system)
    path('pricing/', include('pricing.urls')),
    
    # Django app URLs
    path('api/courses/', include('courses.urls')),
    path('api/catalog/', include('catalog.urls')),
    path('api/newsletter/', include('newsletter.urls', namespace='newsletter_api')),
    path('api/users/', include('users.urls', namespace='users_api')),
    path('api/', include('payments.urls')),  # Payments API endpoints
    
    # User authentication and dashboard
    path('', include('users.urls')),
    
    # Newsletter URLs (direct access)
    path('newsletter/', include('newsletter.urls')),
    
    # Slideshow API
    path('api/slideshow/', include('slideshow.urls')),
]

# Debug-only routes — never expose in production
if settings.DEBUG:
    _i18n_patterns.append(
        path('debug/video/<int:session_id>/', views.debug_video, name='debug_video'),
    )

urlpatterns += i18n_patterns(
    *_i18n_patterns,
    prefix_default_language=False,
)
