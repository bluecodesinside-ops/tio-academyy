from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
import stripe
import json
import logging
from decimal import Decimal
from .models import PricingPackage, Subscription, PaymentSettings, GuaranteeContent, PaymentLog
from programs.models import Video, UserVideoAccess

logger = logging.getLogger(__name__)
User = get_user_model()


def pricing_page(request):
    """Display the pricing page with all packages"""
    packages = PricingPackage.objects.filter(is_active=True).order_by('display_order')
    guarantee_content = GuaranteeContent.get_content()
    
    context = {
        'packages': packages,
        'guarantee_content': guarantee_content,
        'page_title': 'Choose Your Plan - Tio Academy',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Pricing', 'url': None}
        ]
    }
    return render(request, 'pricing/pricing_page.html', context)


def checkout(request, package_slug):
    """Checkout page for selected package"""
    package = get_object_or_404(PricingPackage, slug=package_slug, is_active=True)
    payment_settings = PaymentSettings.get_settings()
    
    # Set Stripe API key
    stripe.api_key = payment_settings.stripe_secret_key
    
    context = {
        'package': package,
        'stripe_publishable_key': payment_settings.stripe_publishable_key,
        'page_title': f'Checkout - {package.name}',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Pricing', 'url': '/pricing/'},
            {'name': f'Checkout - {package.name}', 'url': None}
        ]
    }
    return render(request, 'pricing/checkout.html', context)


@require_POST
def create_checkout_session(request, package_slug):
    """Create Stripe checkout session"""
    package = get_object_or_404(PricingPackage, slug=package_slug, is_active=True)
    payment_settings = PaymentSettings.get_settings()
    
    try:
        # Set Stripe API key
        stripe.api_key = payment_settings.stripe_secret_key
        
        # Get billing cycle (default to monthly)
        billing_cycle = request.POST.get('billing_cycle', 'monthly')
        price_id = (
            package.stripe_monthly_price_id if billing_cycle == 'monthly' 
            else package.stripe_yearly_price_id
        )
        
        if not price_id:
            return JsonResponse({
                'error': 'Price ID not configured for this package'
            }, status=400)
        
        # Create or get customer
        customer_email = request.POST.get('email')
        if not customer_email:
            return JsonResponse({
                'error': 'Email is required'
            }, status=400)
        
        # Check if user is authenticated
        if request.user.is_authenticated:
            customer_email = request.user.email
        
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=customer_email,
            metadata={
                'package_name': package.name,
                'billing_cycle': billing_cycle,
            }
        )
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri('/payment-success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri('/payment-cancel/'),
            metadata={
                'package_id': package.id,
                'billing_cycle': billing_cycle,
                'user_id': request.user.id if request.user.is_authenticated else None,
            }
        )
        
        # Log the event
        PaymentLog.objects.create(
            event_type='webhook_received',
            user=request.user if request.user.is_authenticated else None,
            stripe_event_id=checkout_session.id,
            metadata={
                'package_name': package.name,
                'billing_cycle': billing_cycle,
                'checkout_session_id': checkout_session.id,
            }
        )
        
        return JsonResponse({
            'checkout_url': checkout_session.url
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_checkout_session: {str(e)}")
        return JsonResponse({
            'error': 'Payment processing error. Please try again.'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in create_checkout_session: {str(e)}")
        return JsonResponse({
            'error': 'An unexpected error occurred. Please try again.'
        }, status=500)


def payment_success(request):
    """Handle successful payment"""
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('pricing:pricing_page')
    
    payment_settings = PaymentSettings.get_settings()
    stripe.api_key = payment_settings.stripe_secret_key
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status != 'paid':
            messages.error(request, 'Payment was not completed successfully.')
            return redirect('pricing:pricing_page')
        
        # Get package and user info
        package_id = session.metadata.get('package_id')
        user_id = session.metadata.get('user_id')
        billing_cycle = session.metadata.get('billing_cycle', 'monthly')
        
        package = get_object_or_404(PricingPackage, id=package_id)
        
        # Get or create user
        if user_id:
            user = get_object_or_404(User, id=user_id)
        else:
            # Create user account for guest checkout
            user_email = session.customer_details.email
            user, created = User.objects.get_or_create(
                email=user_email,
                defaults={'username': user_email.split('@')[0]}
            )
            if created:
                user.set_unusable_password()
                user.save()
        
        # Create subscription
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            package=package,
            defaults={
                'stripe_customer_id': session.customer,
                'stripe_subscription_id': session.subscription,
                'status': 'active',
                'billing_cycle': billing_cycle,
                'current_period_start': timezone.now(),
                'current_period_end': timezone.now() + timezone.timedelta(
                    days=365 if billing_cycle == 'yearly' else 30
                ),
            }
        )
        
        if not created:
            # Update existing subscription
            subscription.stripe_customer_id = session.customer
            subscription.stripe_subscription_id = session.subscription
            subscription.status = 'active'
            subscription.billing_cycle = billing_cycle
            subscription.current_period_start = timezone.now()
            subscription.current_period_end = timezone.now() + timezone.timedelta(
                days=365 if billing_cycle == 'yearly' else 30
            )
            subscription.save()
        
        # Grant video access based on package
        grant_video_access(user, package)
        
        # Log successful payment
        PaymentLog.objects.create(
            event_type='payment_success',
            user=user,
            subscription=subscription,
            stripe_event_id=session_id,
            amount=Decimal(str(session.amount_total / 100)),
            currency=session.currency,
            metadata={
                'package_name': package.name,
                'billing_cycle': billing_cycle,
            }
        )
        
        # Send confirmation email
        send_payment_confirmation_email(user, package, subscription)
        
        messages.success(
            request, 
            f'Payment successful! Welcome to {package.name}. You now have access to all your package features.'
        )
        
        return render(request, 'pricing/payment_success.html', {
            'package': package,
            'subscription': subscription,
            'user': user,
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in payment_success: {str(e)}")
        messages.error(request, 'Payment verification failed. Please contact support.')
        return redirect('pricing:pricing_page')
    
    except Exception as e:
        logger.error(f"Error in payment_success: {str(e)}")
        messages.error(request, 'An unexpected error occurred. Please contact support.')
        return redirect('pricing:pricing_page')


def payment_cancel(request):
    """Handle cancelled payment"""
    messages.info(request, 'Payment was cancelled. You can try again anytime.')
    return render(request, 'pricing/payment_cancel.html')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    payment_settings = PaymentSettings.get_settings()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, payment_settings.stripe_webhook_secret
        )
    except ValueError:
        logger.error("Invalid payload in webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return HttpResponse(status=400)
    
    # Handle the event
    try:
        if event['type'] == 'customer.subscription.created':
            handle_subscription_created(event)
        elif event['type'] == 'customer.subscription.updated':
            handle_subscription_updated(event)
        elif event['type'] == 'customer.subscription.deleted':
            handle_subscription_deleted(event)
        elif event['type'] == 'invoice.payment_succeeded':
            handle_payment_succeeded(event)
        elif event['type'] == 'invoice.payment_failed':
            handle_payment_failed(event)
        else:
            logger.info(f"Unhandled event type: {event['type']}")
    
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return HttpResponse(status=500)
    
    return HttpResponse(status=200)


def handle_subscription_created(event):
    """Handle subscription created webhook"""
    subscription_data = event['data']['object']
    logger.info(f"Subscription created: {subscription_data['id']}")


def handle_subscription_updated(event):
    """Handle subscription updated webhook"""
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        subscription.status = subscription_data['status']
        subscription.current_period_start = timezone.datetime.fromtimestamp(
            subscription_data['current_period_start'], tz=timezone.utc
        )
        subscription.current_period_end = timezone.datetime.fromtimestamp(
            subscription_data['current_period_end'], tz=timezone.utc
        )
        subscription.cancel_at_period_end = subscription_data['cancel_at_period_end']
        subscription.save()
        
        logger.info(f"Subscription updated: {stripe_subscription_id}")
        
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {stripe_subscription_id}")


def handle_subscription_deleted(event):
    """Handle subscription deleted webhook"""
    subscription_data = event['data']['object']
    stripe_subscription_id = subscription_data['id']
    
    try:
        subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription_id)
        subscription.status = 'cancelled'
        subscription.canceled_at = timezone.now()
        subscription.save()
        
        logger.info(f"Subscription cancelled: {stripe_subscription_id}")
        
    except Subscription.DoesNotExist:
        logger.error(f"Subscription not found: {stripe_subscription_id}")


def handle_payment_succeeded(event):
    """Handle successful payment webhook"""
    invoice_data = event['data']['object']
    logger.info(f"Payment succeeded: {invoice_data['id']}")


def handle_payment_failed(event):
    """Handle failed payment webhook"""
    invoice_data = event['data']['object']
    logger.info(f"Payment failed: {invoice_data['id']}")


def grant_video_access(user, package):
    """Grant video access based on package tier"""
    # Define access levels for each package
    access_levels = {
        'standard': ['basic'],
        'pro': ['basic', 'intermediate'],
        'gold': ['basic', 'intermediate', 'advanced'],
    }
    
    allowed_levels = access_levels.get(package.tier, [])
    
    # Get all videos that match the allowed skill levels
    videos = Video.objects.filter(
        skill_level__level__in=allowed_levels,
        is_active=True
    )
    
    # Create access records for all matching videos
    for video in videos:
        UserVideoAccess.objects.get_or_create(
            user=user,
            video=video,
            defaults={
                'payment_id': f'subscription_{package.tier}',
            }
        )


def send_payment_confirmation_email(user, package, subscription):
    """Send payment confirmation email"""
    try:
        subject = f'Welcome to {package.name} - Tio Academy'
        
        context = {
            'user': user,
            'package': package,
            'subscription': subscription,
            'site_url': request.build_absolute_uri('/'),
        }
        
        html_message = render_to_string('pricing/emails/payment_confirmation.html', context)
        text_message = render_to_string('pricing/emails/payment_confirmation.txt', context)
        
        send_mail(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Confirmation email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"Error sending confirmation email: {str(e)}")


@login_required
def my_subscription(request):
    """User's subscription management page"""
    try:
        subscription = Subscription.objects.filter(
            user=request.user,
            status__in=['active', 'trialing']
        ).latest('created_at')
    except Subscription.DoesNotExist:
        subscription = None
    
    context = {
        'subscription': subscription,
        'page_title': 'My Subscription - Tio Academy',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'My Subscription', 'url': None}
        ]
    }
    return render(request, 'pricing/my_subscription.html', context)


@login_required
@require_POST
def cancel_subscription(request):
    """Cancel user's subscription"""
    try:
        subscription = Subscription.objects.get(
            user=request.user,
            status__in=['active', 'trialing']
        )
        
        # Set to cancel at period end
        subscription.cancel_at_period_end = True
        subscription.save()
        
        messages.success(
            request, 
            'Your subscription will be cancelled at the end of the current billing period.'
        )
        
    except Subscription.DoesNotExist:
        messages.error(request, 'No active subscription found.')
    
    return redirect('pricing:my_subscription')