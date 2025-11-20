from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    # Pricing page
    path('', views.pricing_page, name='pricing_page'),
    
    # Checkout flow
    path('checkout/<str:package_slug>/', views.checkout, name='checkout'),
    path('create-checkout-session/<str:package_slug>/', views.create_checkout_session, name='create_checkout_session'),
    
    # Payment results
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Subscription management
    path('my-subscription/', views.my_subscription, name='my_subscription'),
    path('cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    
    # Webhooks
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]

