from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile with Stripe subscription information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Stripe fields
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Subscription status
    SUBSCRIPTION_STATUS_CHOICES = [
        ('inactive', 'Inactive'),
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing'),
    ]
    subscription_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_STATUS_CHOICES,
        default='inactive'
    )
    
    # Lifetime access
    has_lifetime_access = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription_status}"
    
    def has_premium_access(self):
        """Check if user has premium access (active subscription or lifetime access)"""
        return self.subscription_status == 'active' or self.has_lifetime_access


class SiteDailyStat(models.Model):
    """One row per day: visits, buy clicks, and completed purchases."""
    day = models.DateField(unique=True)
    page_views = models.PositiveIntegerField('page opens', default=0)
    unique_visitors = models.PositiveIntegerField('people', default=0)
    buy_clicks = models.PositiveIntegerField('clicked buy', default=0)
    purchases = models.PositiveIntegerField('bought', default=0)

    class Meta:
        ordering = ['-day']
        verbose_name = 'Website traffic day'
        verbose_name_plural = 'Website traffic'

    def __str__(self):
        return str(self.day)


class SiteVisitorDay(models.Model):
    """Anonymous unique visitor for a calendar day (hashed, no personal data)."""
    day = models.DateField(db_index=True)
    visitor_key = models.CharField(max_length=64)

    class Meta:
        unique_together = ('day', 'visitor_key')


class SiteInsightCount(models.Model):
    """Daily totals for devices, pages people open, buy clicks, and paid items."""

    KIND_DEVICE = 'device'
    KIND_PAGE = 'page'
    KIND_COUNTRY = 'country'
    KIND_BUY = 'buy_click'
    KIND_PAY = 'purchase'

    day = models.DateField(db_index=True)
    kind = models.CharField(max_length=20)
    label = models.CharField(max_length=160)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('day', 'kind', 'label')
        ordering = ['-count', 'label']
        verbose_name = 'Website insight'
        verbose_name_plural = 'Website insights'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile automatically when User is created"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Ensure profile exists
            UserProfile.objects.get_or_create(user=instance)
    except Exception:
        # Prevent user save from failing due to profile issues
        pass
