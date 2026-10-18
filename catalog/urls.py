from django.urls import path

from catalog import views

app_name = 'catalog'

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('checkout/dance/', views.checkout_dance_tier, name='checkout_dance'),
    path('checkout/package/', views.checkout_package, name='checkout_package'),
    path('checkout/packages/', views.checkout_packages, name='checkout_packages'),
    path('checkout/bundle/', views.checkout_bundle, name='checkout_bundle'),
    path('me/entitlements/', views.my_entitlements, name='my_entitlements'),
]
