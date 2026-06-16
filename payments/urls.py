from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create-checkout-session/<int:course_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('success/', views.payment_success, name='payment_success'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
    # New API endpoints for subscription and one-time payments
    path('checkout/subscription/', views.checkout_subscription, name='checkout_subscription'),
    path('checkout/onetime/', views.checkout_onetime, name='checkout_onetime'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook_api'),
]






