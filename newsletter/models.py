from django.db import models
from django.utils import timezone

# Create your models here.

class NewsletterSubscription(models.Model):
    """Model for newsletter subscriptions"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    last_email_sent = models.DateTimeField(blank=True, null=True)
    email_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def unsubscribe(self):
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save()
    
    def resubscribe(self):
        self.is_active = True
        self.unsubscribed_at = None
        self.save()
