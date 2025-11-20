from django.contrib import admin
from .models import Payment, UserCourseAccess


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'amount', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'currency']
    search_fields = ['user__username', 'user__email', 'course__title', 'stripe_payment_intent_id']
    readonly_fields = ['stripe_payment_intent_id', 'stripe_session_id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('user', 'course', 'amount', 'currency', 'status')
        }),
        ('Stripe Information', {
            'fields': ('stripe_payment_intent_id', 'stripe_session_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserCourseAccess)
class UserCourseAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'is_active', 'granted_at']
    list_filter = ['is_active', 'granted_at']
    search_fields = ['user__username', 'user__email', 'course__title']
    readonly_fields = ['granted_at']
    ordering = ['-granted_at']
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'course', 'payment', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('granted_at',),
            'classes': ('collapse',)
        }),
    )