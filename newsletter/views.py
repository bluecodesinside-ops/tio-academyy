from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import NewsletterSubscription
import json

# Create your views here.

@require_http_methods(["POST"])
def subscribe(request):
    """Subscribe to newsletter with automatic welcome email"""
    try:
        # Handle both JSON and regular form submissions
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
            
        email = data.get('email')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not email:
            if request.content_type == 'application/json':
                return JsonResponse({'error': 'Email is required'}, status=400)
            else:
                # For regular form submission, redirect back with error message
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.error(request, 'Email is required')
                return redirect('home')
                
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            if request.content_type == 'application/json':
                return JsonResponse({'error': 'Please enter a valid email address'}, status=400)
            else:
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.error(request, 'Please enter a valid email address')
                return redirect('home')
        
        subscription, created = NewsletterSubscription.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True
            }
        )
        
        # Handle success responses
        if request.content_type == 'application/json':
            # JSON response for AJAX requests
            if not created and subscription.is_active:
                return JsonResponse({'message': 'Already subscribed'})
            elif not created and not subscription.is_active:
                subscription.is_active = True
                subscription.unsubscribed_at = None
                subscription.save()
                send_welcome_email(subscription, is_resubscribe=True)
                return JsonResponse({'message': 'Resubscribed successfully'})
            else:
                send_welcome_email(subscription)
                return JsonResponse({'message': 'Subscribed successfully'})
        else:
            # Regular form submission - redirect with success message
            from django.contrib import messages
            from django.shortcuts import redirect
            
            if not created and subscription.is_active:
                messages.info(request, f'✅ {email} is already subscribed to our newsletter!')
            elif not created and not subscription.is_active:
                subscription.is_active = True
                subscription.unsubscribed_at = None
                subscription.save()
                send_welcome_email(subscription, is_resubscribe=True)
                messages.success(request, f'🎉 Welcome back! You have been resubscribed to our newsletter.')
            else:
                send_welcome_email(subscription)
                messages.success(request, f'🎉 Successfully subscribed! Check your email for confirmation.')
            
            return redirect('home')
            
    except Exception as e:
        if request.content_type == 'application/json':
            return JsonResponse({'error': str(e)}, status=500)
        else:
            from django.contrib import messages
            from django.shortcuts import redirect
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('home')

@csrf_exempt
@require_http_methods(["POST"])
def unsubscribe(request):
    """Unsubscribe from newsletter"""
    try:
        data = json.loads(request.body) if request.body else request.POST
        email = data.get('email')
        
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        
        subscription = NewsletterSubscription.objects.get(email=email)
        subscription.unsubscribe()
        return JsonResponse({'message': 'Unsubscribed successfully'})
    except NewsletterSubscription.DoesNotExist:
        return JsonResponse({'error': 'Email not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def send_welcome_email(subscription, is_resubscribe=False):
    """Send welcome email to new subscribers"""
    subject = "Welcome to Latina Dance Academy Newsletter!" if not is_resubscribe else "Welcome Back to Latina Dance Academy!"
    
    # Create HTML email content
    html_content = render_to_string('newsletter/emails/welcome.html', {
        'subscription': subscription,
        'is_resubscribe': is_resubscribe
    })
    
    # Create plain text version
    text_content = render_to_string('newsletter/emails/welcome.txt', {
        'subscription': subscription,
        'is_resubscribe': is_resubscribe
    })
    
    try:
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscription.email],
            reply_to=[settings.DEFAULT_FROM_EMAIL]
        )
        email.content_subtype = "html"
        email.send()
        
        # Update subscription stats
        subscription.last_email_sent = timezone.now()
        subscription.email_count += 1
        subscription.save()
        
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

def send_newsletter_to_all(subject, html_content, text_content):
    """Send newsletter to all active subscribers"""
    active_subscribers = NewsletterSubscription.objects.filter(is_active=True)
    
    for subscriber in active_subscribers:
        try:
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscriber.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL]
            )
            email.content_subtype = "html"
            email.send()
            
            # Update stats
            subscriber.last_email_sent = timezone.now()
            subscriber.email_count += 1
            subscriber.save()
            
        except Exception as e:
            print(f"Failed to send email to {subscriber.email}: {e}")
    
    return len(active_subscribers)
