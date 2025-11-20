from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import PricingPackage, Subscription, PaymentSettings, GuaranteeContent, PaymentLog


class PricingPackageAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'tier', 'monthly_price', 'yearly_price', 
        'yearly_discount', 'is_popular', 'is_active', 'display_order'
    ]
    list_filter = ['tier', 'is_popular', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_popular', 'is_active', 'display_order']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'tier', 'description', 'display_order', 'is_active')
        }),
        ('Pricing', {
            'fields': ('monthly_price', 'yearly_price', 'button_text')
        }),
        ('Features', {
            'fields': ('features',),
            'description': 'Enter features as a JSON array, e.g., ["Feature 1", "Feature 2", "Feature 3"]'
        }),
        ('Stripe Integration', {
            'fields': ('stripe_monthly_price_id', 'stripe_yearly_price_id'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_popular',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def yearly_discount(self, obj):
        discount = obj.get_yearly_discount_percentage()
        if discount > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}% OFF</span>',
                discount
            )
        return "-"
    yearly_discount.short_description = "Yearly Discount"
    
    actions = ['activate_selected', 'deactivate_selected', 'mark_popular', 'unmark_popular']
    
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} packages activated.')
    activate_selected.short_description = "Activate selected packages"
    
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} packages deactivated.')
    deactivate_selected.short_description = "Deactivate selected packages"
    
    def mark_popular(self, request, queryset):
        # Only allow one popular package
        queryset.update(is_popular=False)
        updated = queryset.update(is_popular=True)
        self.message_user(request, f'{updated} package marked as popular.')
    mark_popular.short_description = "Mark as popular (only one allowed)"
    
    def unmark_popular(self, request, queryset):
        updated = queryset.update(is_popular=False)
        self.message_user(request, f'{updated} packages unmarked as popular.')
    unmark_popular.short_description = "Unmark as popular"


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'package', 'status', 'billing_cycle', 
        'current_period_end', 'is_active', 'created_at'
    ]
    list_filter = [
        'package', 'status', 'billing_cycle', 'cancel_at_period_end', 'created_at'
    ]
    search_fields = [
        'user__username', 'user__email', 'stripe_customer_id', 'stripe_subscription_id'
    ]
    readonly_fields = [
        'stripe_customer_id', 'stripe_subscription_id', 'stripe_payment_method_id',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('User & Package', {
            'fields': ('user', 'package')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id', 'stripe_payment_method_id'),
            'classes': ('collapse',)
        }),
        ('Subscription Details', {
            'fields': ('status', 'billing_cycle', 'current_period_start', 'current_period_end')
        }),
        ('Cancellation', {
            'fields': ('cancel_at_period_end', 'canceled_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active(self, obj):
        if obj.is_active():
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active.short_description = "Status"
    
    actions = ['cancel_subscriptions', 'reactivate_subscriptions']
    
    def cancel_subscriptions(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} subscriptions cancelled.')
    cancel_subscriptions.short_description = "Cancel selected subscriptions"
    
    def reactivate_subscriptions(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} subscriptions reactivated.')
    reactivate_subscriptions.short_description = "Reactivate selected subscriptions"


class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ['is_live_mode', 'success_redirect_url', 'cancel_redirect_url', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Stripe Configuration', {
            'fields': ('stripe_publishable_key', 'stripe_secret_key', 'stripe_webhook_secret')
        }),
        ('PayPal Configuration (Optional)', {
            'fields': ('paypal_client_id', 'paypal_secret'),
            'classes': ('collapse',)
        }),
        ('Environment Settings', {
            'fields': ('is_live_mode',)
        }),
        ('Redirect URLs', {
            'fields': ('success_redirect_url', 'cancel_redirect_url')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not PaymentSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the only instance
        return False


class GuaranteeContentAdmin(admin.ModelAdmin):
    list_display = ['headline', 'days', 'customer_count', 'star_rating', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('headline', 'description', 'days')
        }),
        ('Trust Elements', {
            'fields': ('customer_count', 'star_rating'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'icon', 'background_color')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not GuaranteeContent.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the only instance
        return False


class PaymentLogAdmin(admin.ModelAdmin):
    list_display = [
        'event_type', 'user', 'subscription', 'amount', 'currency', 'created_at'
    ]
    list_filter = ['event_type', 'currency', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'stripe_event_id', 'subscription__package__name'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'user', 'subscription', 'stripe_event_id')
        }),
        ('Payment Details', {
            'fields': ('amount', 'currency')
        }),
        ('Additional Data', {
            'fields': ('metadata', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        # Logs are created programmatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Logs should not be modified
        return False


# Register all models
admin.site.register(PricingPackage, PricingPackageAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(PaymentSettings, PaymentSettingsAdmin)
admin.site.register(GuaranteeContent, GuaranteeContentAdmin)
admin.site.register(PaymentLog, PaymentLogAdmin)