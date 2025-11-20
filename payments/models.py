from django.db import models
from django.contrib.auth.models import User
from courses.models import Course


class Payment(models.Model):
    """Model to track course payments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='usd')
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} - ${self.amount}"


class UserCourseAccess(models.Model):
    """Model to track which courses a user has access to"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_access')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='user_access')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='access_granted')
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title}"