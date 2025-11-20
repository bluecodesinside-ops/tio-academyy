from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.core.exceptions import ValidationError
import json


class PricingPackage(models.Model):
    """Model for subscription packages (Standard, Pro, Gold)"""
    PACKAGE_TIERS = [
        ('standard', 'Standard'),
        ('pro', 'Pro'),
        ('gold', 'Gold'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    tier = models.CharField(max_length=20, choices=PACKAGE_TIERS, unique=True)
    description = models.TextField(blank=True, help_text="Brief description of the package")
    
    # Pricing
    monthly_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monthly subscription price in USD"
    )
    yearly_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True, 
        blank=True,
        help_text="Yearly subscription price in USD (optional)"
    )
    
    # Features (stored as JSON)
    features = models.JSONField(
        default=list,
        help_text="List of features included in this package"
    )
    
    # Stripe Integration
    stripe_monthly_price_id = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Stripe Price ID for monthly subscription"
    )
    stripe_yearly_price_id = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Stripe Price ID for yearly subscription"
    )
    
    # Display Settings
    is_popular = models.BooleanField(
        default=False,
        help_text="Mark as 'Most Popular' on pricing page"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Show this package on pricing page"
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order of display on pricing page"
    )
    button_text = models.CharField(
        max_length=50,
        default="Choose Plan",
        help_text="Text for the CTA button"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Pricing Package"
        verbose_name_plural = "Pricing Packages"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_yearly_discount_percentage(self):
        """Calculate yearly discount percentage"""
        if self.yearly_price and self.monthly_price:
            monthly_yearly = self.monthly_price * 12
            if monthly_yearly > 0:
                discount = ((monthly_yearly - self.yearly_price) / monthly_yearly) * 100
                return round(discount, 1)
        return 0
    
    def get_features_list(self):
        """Return features as a list"""
        if isinstance(self.features, str):
            try:
                return json.loads(self.features)
            except json.JSONDecodeError:
                return []
        return self.features or []
    
    def clean(self):
        super().clean()
        if self.yearly_price and self.monthly_price:
            if self.yearly_price >= (self.monthly_price * 12):
                raise ValidationError("Yearly price should be less than 12 months of monthly price")


class Subscription(models.Model):
    """Model for user subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('trialing', 'Trialing'),
        ('unpaid', 'Unpaid'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(PricingPackage, on_delete=models.CASCADE, related_name='subscriptions')
    
    # Stripe Integration
    stripe_customer_id = models.CharField(max_length=200, blank=True)
    stripe_subscription_id = models.CharField(max_length=200, unique=True, blank=True)
    stripe_payment_method_id = models.CharField(max_length=200, blank=True)
    
    # Subscription Details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='incomplete')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # Billing
    billing_cycle = models.CharField(
        max_length=10,
        choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
    
    def __str__(self):
        return f"{self.user.username} - {self.package.name} ({self.status})"
    
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in ['active', 'trialing']
    
    def is_expired(self):
        """Check if subscription has expired"""
        return self.status in ['expired', 'cancelled', 'incomplete_expired']
    
    def get_remaining_days(self):
        """Get remaining days in current period"""
        if self.current_period_end:
            from django.utils import timezone
            now = timezone.now()
            if self.current_period_end > now:
                return (self.current_period_end - now).days
        return 0


class PaymentSettings(models.Model):
    """Singleton model for payment configuration"""
    # Stripe Configuration
    stripe_publishable_key = models.CharField(
        max_length=200,
        help_text="Stripe Publishable Key"
    )
    stripe_secret_key = models.CharField(
        max_length=200,
        help_text="Stripe Secret Key"
    )
    stripe_webhook_secret = models.CharField(
        max_length=200,
        blank=True,
        help_text="Stripe Webhook Secret"
    )
    
    # PayPal Configuration (Optional)
    paypal_client_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="PayPal Client ID"
    )
    paypal_secret = models.CharField(
        max_length=200,
        blank=True,
        help_text="PayPal Secret"
    )
    
    # Environment Settings
    is_live_mode = models.BooleanField(
        default=False,
        help_text="Use live Stripe keys (uncheck for test mode)"
    )
    
    # Redirect URLs
    success_redirect_url = models.URLField(
        default='/payment-success/',
        help_text="URL to redirect after successful payment"
    )
    cancel_redirect_url = models.URLField(
        default='/pricing/',
        help_text="URL to redirect after cancelled payment"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payment Settings"
        verbose_name_plural = "Payment Settings"
    
    def __str__(self):
        return f"Payment Settings ({'Live' if self.is_live_mode else 'Test'} Mode)"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and PaymentSettings.objects.exists():
            raise ValidationError("Only one PaymentSettings instance is allowed")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get the single PaymentSettings instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class GuaranteeContent(models.Model):
    """Model for money-back guarantee content"""
    headline = models.CharField(
        max_length=200,
        default="100% Money-Back Guarantee"
    )
    description = models.TextField(
        default="Try our program risk-free for 30 days. If you're not completely satisfied, we'll refund your money - no questions asked."
    )
    days = models.PositiveIntegerField(
        default=30,
        help_text="Number of days for the guarantee"
    )
    
    # Trust Elements
    customer_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of satisfied customers (e.g., 10000)"
    )
    star_rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Average star rating (0-5)"
    )
    
    # Display Settings
    is_active = models.BooleanField(
        default=True,
        help_text="Show guarantee section on pricing page"
    )
    icon = models.CharField(
        max_length=50,
        default="fas fa-shield-alt",
        help_text="Font Awesome icon class"
    )
    background_color = models.CharField(
        max_length=7,
        default="#10B981",
        help_text="Background color in hex format"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Guarantee Content"
        verbose_name_plural = "Guarantee Content"
    
    def __str__(self):
        return f"Guarantee Content ({self.days} days)"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and GuaranteeContent.objects.exists():
            raise ValidationError("Only one GuaranteeContent instance is allowed")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_content(cls):
        """Get the single GuaranteeContent instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class PaymentLog(models.Model):
    """Model for logging payment events"""
    EVENT_TYPES = [
        ('payment_success', 'Payment Success'),
        ('payment_failed', 'Payment Failed'),
        ('subscription_created', 'Subscription Created'),
        ('subscription_updated', 'Subscription Updated'),
        ('subscription_cancelled', 'Subscription Cancelled'),
        ('webhook_received', 'Webhook Received'),
        ('refund_processed', 'Refund Processed'),
    ]
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='payment_logs'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_logs'
    )
    
    # Event Details
    stripe_event_id = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=3, default='usd')
    
    # Additional Data
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment Log"
        verbose_name_plural = "Payment Logs"
    
    def __str__(self):
        return f"{self.event_type} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"