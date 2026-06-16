import stripe
import json
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import Payment, UserCourseAccess
from courses.models import Course
from users.models import UserProfile

# Set Stripe API key (will be overridden in functions if needed)
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request, course_id):
    """Create a Stripe checkout session for course purchase"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user already has access to this course
    if UserCourseAccess.objects.filter(user=request.user, course=course, is_active=True).exists():
        messages.info(request, f'You already have access to {course.title}!')
        return redirect('course_detail', course_id=course_id)
    
    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': course.title,
                        'description': course.description,
                    },
                    'unit_amount': int(course.price * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(f'/payments/success/?session_id={{CHECKOUT_SESSION_ID}}'),
            cancel_url=request.build_absolute_uri(f'/courses/{course_id}/'),
            metadata={
                'course_id': course_id,
                'user_id': request.user.id,
            }
        )
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            stripe_payment_intent_id=checkout_session.payment_intent,
            stripe_session_id=checkout_session.id,
            amount=course.price,
            status='pending'
        )
        
        return JsonResponse({'checkout_url': checkout_session.url})
        
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('course_detail', course_id=course_id)
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('course_detail', course_id=course_id)


@login_required
def payment_success(request):
    """Handle successful payment - redirect to dashboard"""
    session_id = request.GET.get('session_id')
    
    if session_id:
        try:
            # Retrieve the checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                messages.success(request, 'Payment successful! Your access has been activated.')
        except:
            pass
    
    return redirect('users:dashboard')


@csrf_exempt
def stripe_webhook(request):
    """
    Handle Stripe webhooks for payment confirmation and subscription management.
    
    Events handled:
    - checkout.session.completed: Grant access after successful payment
    - invoice.paid: Activate subscription after invoice payment
    - customer.subscription.deleted: Revoke access when subscription is canceled
    - customer.subscription.updated: Update subscription status
    """
    import logging
    
    logger = logging.getLogger(__name__)
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not settings.STRIPE_WEBHOOK_SECRET or not settings.STRIPE_SECRET_KEY:
        logger.error('Stripe webhook secret or secret key not configured')
        return HttpResponse(status=500)
    
    # Set Stripe API key
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f'Invalid payload: {e}')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Invalid signature: {e}')
        return HttpResponse(status=400)
    
    event_type = event['type']
    logger.info(f'Received Stripe webhook event: {event_type}')
    
    # Helper function to find user by customer ID or email
    def find_user_by_customer_id(customer_id):
        """Find user by Stripe customer ID"""
        try:
            profile = UserProfile.objects.get(stripe_customer_id=customer_id)
            return profile.user
        except UserProfile.DoesNotExist:
            return None
    
    def find_user_by_email(email):
        """Find user by email address"""
        from django.contrib.auth.models import User
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    # Handle checkout.session.completed
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        logger.info(f'Processing checkout.session.completed for session: {session.get("id")}')
        
        # Method 1: Get user from metadata (preferred)
        user_id = session.get('metadata', {}).get('user_id')
        payment_type = session.get('metadata', {}).get('payment_type')
        
        user = None
        if user_id:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(id=int(user_id))
            except (User.DoesNotExist, ValueError, TypeError):
                pass
        
        # Method 2: Find user by customer ID
        if not user and session.get('customer'):
            user = find_user_by_customer_id(session.get('customer'))
        
        # Method 3: Find user by customer email
        if not user and session.get('customer_details', {}).get('email'):
            user = find_user_by_email(session.get('customer_details', {}).get('email'))
        
        if user:
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Update Stripe customer ID if not set
            if not profile.stripe_customer_id and session.get('customer'):
                profile.stripe_customer_id = session.get('customer')
            
            if payment_type == 'subscription':
                # Subscription payment
                subscription_id = session.get('subscription')
                if subscription_id:
                    profile.subscription_status = 'active'
                    profile.stripe_subscription_id = subscription_id
                    profile.save()
                    logger.info(f'Activated subscription for user {user.email}: {subscription_id}')
            elif payment_type == 'lifetime':
                # One-time lifetime payment
                profile.has_lifetime_access = True
                profile.save()
                logger.info(f'Granted lifetime access to user {user.email}')
            elif session.get('mode') == 'subscription':
                # Subscription checkout without explicit payment_type
                subscription_id = session.get('subscription')
                if subscription_id:
                    profile.subscription_status = 'active'
                    profile.stripe_subscription_id = subscription_id
                    profile.save()
                    logger.info(f'Activated subscription for user {user.email}: {subscription_id}')
            elif session.get('mode') == 'payment':
                # One-time payment without explicit payment_type
                profile.has_lifetime_access = True
                profile.save()
                logger.info(f'Granted lifetime access to user {user.email}')
        else:
            logger.warning(f'Could not find user for checkout session: {session.get("id")}')
        
        # Legacy: Handle course-specific payments
        try:
            payment = Payment.objects.get(stripe_session_id=session['id'])
            if session['payment_status'] == 'paid':
                payment.status = 'succeeded'
                payment.save()
                
                # Grant course access if not already granted
                if not UserCourseAccess.objects.filter(
                    user=payment.user, 
                    course=payment.course, 
                    is_active=True
                ).exists():
                    UserCourseAccess.objects.create(
                        user=payment.user,
                        course=payment.course,
                        payment=payment
                    )
                    logger.info(f'Granted course access to user {payment.user.email} for course {payment.course.title}')
        except Payment.DoesNotExist:
            pass
    
    # Handle invoice.paid (for subscription renewals)
    elif event_type == 'invoice.paid':
        invoice = event['data']['object']
        logger.info(f'Processing invoice.paid for invoice: {invoice.get("id")}')
        
        subscription_id = invoice.get('subscription')
        customer_id = invoice.get('customer')
        
        if subscription_id and customer_id:
            # Find user by customer ID
            user = find_user_by_customer_id(customer_id)
            
            if user:
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Update subscription status to active
                if profile.stripe_subscription_id == subscription_id:
                    profile.subscription_status = 'active'
                    profile.save()
                    logger.info(f'Activated subscription for user {user.email} after invoice payment')
            else:
                # Try to find by email
                customer = stripe.Customer.retrieve(customer_id)
                if customer.get('email'):
                    user = find_user_by_email(customer.get('email'))
                    if user:
                        profile, created = UserProfile.objects.get_or_create(user=user)
                        profile.stripe_customer_id = customer_id
                        profile.stripe_subscription_id = subscription_id
                        profile.subscription_status = 'active'
                        profile.save()
                        logger.info(f'Activated subscription for user {user.email} after invoice payment')
    
    # Handle customer.subscription.deleted
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        subscription_id = subscription.get('id')
        logger.info(f'Processing customer.subscription.deleted for subscription: {subscription_id}')
        
        try:
            profile = UserProfile.objects.get(stripe_subscription_id=subscription_id)
            profile.subscription_status = 'canceled'
            profile.save()
            logger.info(f'Canceled subscription for user {profile.user.email}')
        except UserProfile.DoesNotExist:
            logger.warning(f'Could not find user profile for subscription: {subscription_id}')
    
    # Handle customer.subscription.updated (for status changes)
    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        subscription_id = subscription.get('id')
        status = subscription.get('status')
        logger.info(f'Processing customer.subscription.updated for subscription: {subscription_id}, status: {status}')
        
        try:
            profile = UserProfile.objects.get(stripe_subscription_id=subscription_id)
            
            # Map Stripe subscription status to our status
            status_mapping = {
                'active': 'active',
                'canceled': 'canceled',
                'past_due': 'past_due',
                'trialing': 'trialing',
                'unpaid': 'inactive',
                'incomplete': 'inactive',
                'incomplete_expired': 'inactive',
            }
            
            profile.subscription_status = status_mapping.get(status, 'inactive')
            profile.save()
            logger.info(f'Updated subscription status for user {profile.user.email} to {profile.subscription_status}')
        except UserProfile.DoesNotExist:
            logger.warning(f'Could not find user profile for subscription: {subscription_id}')
    
    # Return 200 OK to acknowledge receipt
    return HttpResponse(status=200)


@login_required
def checkout_subscription(request):
    """Create Stripe checkout session for subscription - LOGIN REQUIRED
    Accepts both GET (after login redirect) and POST (direct form submission)
    """
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_SUB:
        messages.error(request, 'Stripe configuration missing')
        return redirect('users:dashboard')
    
    # Set Stripe API key
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Create or get Stripe customer
        customer_id = profile.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={'user_id': request.user.id}
            )
            customer_id = customer.id
            profile.stripe_customer_id = customer_id
            profile.save()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': settings.STRIPE_PRICE_SUB,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri('/dashboard/?session_id={CHECKOUT_SESSION_ID}'),
            cancel_url=request.build_absolute_uri('/dashboard/'),
            metadata={
                'user_id': str(request.user.id),
                'payment_type': 'subscription',
            }
        )
        
        # Debug: Verify the price being used
        price_info = stripe.Price.retrieve(settings.STRIPE_PRICE_SUB)
        print(f"DEBUG: Using price {settings.STRIPE_PRICE_SUB} = ${price_info.unit_amount / 100}/month")
        
        # Redirect directly to Stripe checkout
        return redirect(checkout_session.url)
        
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('users:dashboard')
    except Exception as e:
        import traceback
        messages.error(request, f'An error occurred: {str(e)}')
        print(f"Checkout subscription error: {traceback.format_exc()}")
        return redirect('users:dashboard')


@login_required
def checkout_onetime(request):
    """Create Stripe checkout session for one-time lifetime payment - LOGIN REQUIRED
    Accepts both GET (after login redirect) and POST (direct form submission)
    """
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ONE_TIME:
        messages.error(request, 'Stripe configuration missing')
        return redirect('users:dashboard')
    
    # Set Stripe API key
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Create or get Stripe customer
        customer_id = profile.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={'user_id': request.user.id}
            )
            customer_id = customer.id
            profile.stripe_customer_id = customer_id
            profile.save()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': settings.STRIPE_PRICE_ONE_TIME,
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/dashboard/?session_id={CHECKOUT_SESSION_ID}'),
            cancel_url=request.build_absolute_uri('/dashboard/'),
            metadata={
                'user_id': str(request.user.id),
                'payment_type': 'lifetime',
            }
        )
        
        # Redirect directly to Stripe checkout
        return redirect(checkout_session.url)
        
    except stripe.error.StripeError as e:
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('users:dashboard')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('users:dashboard')


def check_course_access(user, course):
    """Check if user has access to a course"""
    # Check premium access (subscription or lifetime)
    if user.is_authenticated:
        try:
            profile = user.profile
            if profile.has_premium_access():
                return True
        except UserProfile.DoesNotExist:
            pass
    
    # Check course-specific access (legacy)
    return UserCourseAccess.objects.filter(
        user=user, 
        course=course, 
        is_active=True
    ).exists()