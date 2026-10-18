import stripe
import json
import logging
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from .models import Payment, UserCourseAccess
from courses.models import Course
from users.models import UserProfile

logger = logging.getLogger(__name__)

# Set Stripe API key (will be overridden in functions if needed)
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


def _wants_json(request):
    accept = request.headers.get('Accept', '')
    content_type = request.headers.get('Content-Type', '')
    return (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in accept
        or content_type.startswith('application/json')
    )


def _email_from_stripe_session(session):
    """Pull buyer email from a Stripe Checkout session object/dict."""
    if not session:
        return None
    # stripe.Session objects support attribute + dict access
    details = getattr(session, 'customer_details', None) or (session.get('customer_details') if isinstance(session, dict) else None)
    if details:
        email = details.get('email') if isinstance(details, dict) else getattr(details, 'email', None)
        if email:
            return email.strip().lower()
    email = getattr(session, 'customer_email', None) or (session.get('customer_email') if isinstance(session, dict) else None)
    return email.strip().lower() if email else None


def _user_email(user):
    return (getattr(user, 'email', None) or '').strip().lower()


def resolve_checkout_user(session, metadata=None):
    """
    Resolve or create a Django user for a Stripe checkout.
    Access follows the Stripe payer email, never a mismatched metadata user_id.

    Returns:
        (user, created) — created=True only when a brand-new User row was created.
        Never auto-login existing accounts from email alone (account-takeover risk).
    """
    metadata = metadata or {}
    if isinstance(session, dict):
        metadata = metadata or session.get('metadata') or {}
    else:
        metadata = metadata or (getattr(session, 'metadata', None) or {})

    payer_email = _email_from_stripe_session(session)

    user_id = metadata.get('user_id') if metadata else None
    if user_id and payer_email:
        try:
            candidate = User.objects.get(id=int(user_id))
        except (User.DoesNotExist, ValueError, TypeError):
            candidate = None
        if candidate and _user_email(candidate) == payer_email:
            UserProfile.objects.get_or_create(user=candidate)
            return candidate, False

    customer_id = getattr(session, 'customer', None) or (session.get('customer') if isinstance(session, dict) else None)
    if customer_id:
        try:
            owner = UserProfile.objects.get(stripe_customer_id=customer_id).user
        except UserProfile.DoesNotExist:
            owner = None
        if owner and (not payer_email or _user_email(owner) == payer_email):
            return owner, False

    email = payer_email
    if not email:
        return None, False

    user = User.objects.filter(email__iexact=email).first()
    if user:
        UserProfile.objects.get_or_create(user=user)
        return user, False

    base = ''.join(ch for ch in email.split('@')[0] if ch.isalnum() or ch in '._-')[:30] or 'student'
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{suffix}'
        suffix += 1

    user = User(username=username, email=email)
    user.set_unusable_password()
    user.save()
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if customer_id and not profile.stripe_customer_id:
        profile.stripe_customer_id = customer_id
        profile.save(update_fields=['stripe_customer_id'])
    return user, True


def fulfill_paid_session(session, user=None):
    """Grant catalog/course access for a paid Stripe Checkout session."""
    metadata = getattr(session, 'metadata', None) or (session.get('metadata') if isinstance(session, dict) else {}) or {}
    payment_status = getattr(session, 'payment_status', None) or (session.get('payment_status') if isinstance(session, dict) else None)
    if payment_status not in ('paid', 'no_payment_required'):
        return None
    if user is not None and _email_from_stripe_session(session) and _user_email(user) != _email_from_stripe_session(session):
        user = None
    if user is None:
        user, _ = resolve_checkout_user(session, metadata)
    if not user:
        return None
    payment_type = metadata.get('payment_type')
    session_id = getattr(session, 'id', None) or (session.get('id') if isinstance(session, dict) else '')
    if payment_type == 'catalog':
        from catalog.models import UserAccessEntitlement
        from catalog.services.access import grant_from_stripe_session
        existed = bool(session_id) and UserAccessEntitlement.objects.filter(stripe_session_id=session_id).exists()
        result = grant_from_stripe_session(session, user=user)
        if result and not existed:
            try:
                from users.stats import record_purchase
                record_purchase(metadata.get('item_name') or 'Catalog purchase')
            except Exception:
                pass
        return result
    if payment_type == 'course' or metadata.get('course_id'):
        from .models import Payment
        existed = bool(session_id) and Payment.objects.filter(stripe_session_id=session_id, status='succeeded').exists()
        result = grant_course_access_from_session(session, user=user)
        if result and not existed:
            try:
                from users.stats import record_purchase
                record_purchase(metadata.get('item_name') or 'Course purchase')
            except Exception:
                pass
        return result
    return None


def sync_paid_access_for_user(user):
    """Unlock any paid Stripe checkouts for this user that the webhook missed."""
    if not user or not getattr(user, 'is_authenticated', True) or not settings.STRIPE_SECRET_KEY:
        return 0
    email = (getattr(user, 'email', None) or '').strip().lower()
    if not email:
        return 0
    stripe.api_key = settings.STRIPE_SECRET_KEY
    granted = 0
    try:
        sessions = stripe.checkout.Session.list(limit=40).data
    except Exception:
        logger.exception('Could not list Stripe checkouts for %s', email)
        return 0
    for item in sessions:
        if getattr(item, 'payment_status', None) != 'paid':
            continue
        details = getattr(item, 'customer_details', None) or {}
        item_email = ''
        if isinstance(details, dict):
            item_email = (details.get('email') or '')
        else:
            item_email = getattr(details, 'email', None) or ''
        item_email = (item_email or getattr(item, 'customer_email', None) or '').strip().lower()
        if item_email != email:
            continue
        if fulfill_paid_session(item, user=user):
            granted += 1
    return granted


def grant_course_access_from_session(session, user=None):
    """Mark Payment succeeded and grant UserCourseAccess for a course checkout."""
    metadata = getattr(session, 'metadata', None) or (session.get('metadata') if isinstance(session, dict) else {}) or {}
    session_id = getattr(session, 'id', None) or session.get('id')
    payment_status = getattr(session, 'payment_status', None) or session.get('payment_status')
    payment_intent = getattr(session, 'payment_intent', None) or session.get('payment_intent')
    course_id = metadata.get('course_id')

    if payment_status not in ('paid', 'no_payment_required'):
        return None

    if user is None:
        user, _ = resolve_checkout_user(session, metadata)
    if not user:
        logger.warning('Cannot grant course access — no user for session %s', session_id)
        return None

    course = None
    if course_id:
        course = Course.objects.filter(id=course_id).first()

    payment = Payment.objects.filter(stripe_session_id=session_id).first()
    if payment:
        payment.user = user
        payment.status = 'succeeded'
        if payment_intent:
            payment.stripe_payment_intent_id = payment_intent
        payment.save()
        course = course or payment.course
    elif course:
        amount_total = getattr(session, 'amount_total', None) or session.get('amount_total') or 0
        payment = Payment.objects.create(
            user=user,
            course=course,
            stripe_payment_intent_id=payment_intent or session_id,
            stripe_session_id=session_id,
            amount=(amount_total or 0) / 100,
            status='succeeded',
        )
    else:
        return None

    access, _ = UserCourseAccess.objects.get_or_create(
        user=user,
        course=course,
        defaults={'payment': payment, 'is_active': True},
    )
    if not access.is_active:
        access.is_active = True
        access.payment = payment
        access.save(update_fields=['is_active', 'payment'])
    return course


def create_checkout_session(request, course_id):
    """Create a Stripe checkout session for a single course purchase (guest OK)."""
    course = get_object_or_404(Course, id=course_id, is_active=True)

    if getattr(course, 'sell_as_packets', False):
        if _wants_json(request):
            return JsonResponse(
                {'error': 'Buy a packet on the course page. This course is not sold as one price.'},
                status=400,
            )
        messages.info(request, 'Buy a packet on the course page.')
        return redirect('course_detail', course_id=course_id)

    if course.price is None or course.price <= 0:
        if _wants_json(request):
            return JsonResponse({'error': 'This course is free — no payment required.'}, status=400)
        messages.info(request, 'This course is free — no payment required.')
        return redirect('course_detail', course_id=course_id)

    if request.user.is_authenticated and UserCourseAccess.objects.filter(
        user=request.user, course=course, is_active=True
    ).exists():
        if _wants_json(request):
            return JsonResponse({'error': 'You already have access to this course.', 'redirect': f'/course/{course_id}/'}, status=400)
        messages.info(request, f'You already have access to {course.title or "this course"}!')
        return redirect('course_detail', course_id=course_id)

    if not settings.STRIPE_SECRET_KEY:
        if _wants_json(request):
            return JsonResponse({'error': 'Payments are not configured.'}, status=500)
        messages.error(request, 'Payments are not configured.')
        return redirect('course_detail', course_id=course_id)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    product_name = (course.title or '').strip() or f'Course #{course.id}'
    product_description = (course.description or '').strip() or 'Tio Academy course access'

    metadata = {
        'payment_type': 'course',
        'course_id': str(course_id),
        'item_name': product_name[:160],
    }
    session_kwargs = {
        'payment_method_types': ['card'],
        'line_items': [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': product_name[:120],
                    'description': product_description[:500],
                },
                'unit_amount': int(course.price * 100),
            },
            'quantity': 1,
        }],
        'mode': 'payment',
        'success_url': request.build_absolute_uri('/api/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        'cancel_url': request.build_absolute_uri(f'/course/{course_id}/'),
        'metadata': metadata,
    }

    # Logged-in buyers: prefill email. Guests: Stripe Checkout collects email.
    if request.user.is_authenticated:
        metadata['user_id'] = str(request.user.id)
        if request.user.email:
            session_kwargs['customer_email'] = request.user.email

    try:
        checkout_session = stripe.checkout.Session.create(**session_kwargs)
        try:
            from users.stats import record_buy_click
            record_buy_click(product_name, request)
        except Exception:
            pass

        if request.user.is_authenticated:
            Payment.objects.create(
                user=request.user,
                course=course,
                stripe_payment_intent_id=checkout_session.payment_intent or checkout_session.id,
                stripe_session_id=checkout_session.id,
                amount=course.price,
                status='pending',
            )

        return JsonResponse({'checkout_url': checkout_session.url})

    except stripe.error.StripeError as e:
        if _wants_json(request):
            return JsonResponse({'error': f'Payment error: {e.user_message or str(e)}'}, status=400)
        messages.error(request, f'Payment error: {str(e)}')
        return redirect('course_detail', course_id=course_id)
    except Exception:
        logger.exception('create_checkout_session failed for course %s', course_id)
        if _wants_json(request):
            return JsonResponse({'error': 'Could not start checkout. Please try again.'}, status=500)
        messages.error(request, 'Could not start checkout. Please try again.')
        return redirect('course_detail', course_id=course_id)


def payment_success(request):
    """Verify Stripe checkout and grant access (works for guests too)."""
    session_id = request.GET.get('session_id')
    course_id = None
    catalog_package_id = None

    if session_id and settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        # Encoded/literal Stripe placeholder — look up this buyer's latest paid session.
        if (
            '{CHECKOUT_SESSION_ID}' in session_id
            or '%7BCHECKOUT_SESSION_ID%7D' in session_id
            or not session_id.startswith('cs_')
        ):
            recovered = None
            email = (getattr(request.user, 'email', None) or '').strip()
            if email:
                for item in stripe.checkout.Session.list(limit=30).data:
                    details = item.get('customer_details') or {}
                    item_email = (details.get('email') if isinstance(details, dict) else None) or item.get('customer_email')
                    if item.payment_status == 'paid' and item_email and item_email.lower() == email.lower():
                        recovered = item.id
                        break
            if recovered:
                session_id = recovered
            else:
                logger.error('Checkout success landed with invalid session_id=%s', session_id)
                messages.error(request, 'We could not verify your payment. Contact support if you were charged.')
                session_id = None
    if session_id and settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            metadata = session.get('metadata') or {}
            payment_type = metadata.get('payment_type')
            course_id = metadata.get('course_id')
            catalog_package_id = metadata.get('package_id')

            user, account_created = resolve_checkout_user(session, metadata)
            # Only soft-login brand-new guest accounts. Matching an existing email
            # must NOT log the browser in (prevents account takeover via guest checkout).
            if user and account_created and not request.user.is_authenticated:
                from django.contrib.auth import login
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            if session.payment_status == 'paid':
                if payment_type == 'catalog' and user:
                    from catalog.services.access import grant_from_stripe_session
                    grant_from_stripe_session(session, user=user)
                    messages.success(request, 'Payment successful! Your access is ready.')
                elif payment_type == 'course' or course_id:
                    course = grant_course_access_from_session(session, user=user)
                    if course:
                        course_id = str(course.id)
                    if request.user.is_authenticated or account_created:
                        messages.success(request, 'Payment successful! Your course access is ready.')
                    else:
                        messages.success(
                            request,
                            'Payment successful! Log in with your existing account to watch your course.',
                        )
                elif payment_type == 'lifetime' and user:
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.has_lifetime_access = True
                    if session.get('customer') and not profile.stripe_customer_id:
                        profile.stripe_customer_id = session.get('customer')
                    profile.save()
                    messages.success(request, 'Payment successful! Lifetime access activated.')
                elif payment_type == 'subscription' and user:
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.subscription_status = 'active'
                    if session.get('subscription'):
                        profile.stripe_subscription_id = session.get('subscription')
                    if session.get('customer') and not profile.stripe_customer_id:
                        profile.stripe_customer_id = session.get('customer')
                    profile.save()
                    messages.success(request, 'Payment successful! Your subscription is active.')
                else:
                    messages.success(request, 'Payment successful!')
            else:
                messages.warning(request, 'Payment is still processing. Access will activate shortly.')
        except stripe.error.StripeError as e:
            logger.error('Stripe error verifying checkout session %s: %s', session_id, e)
            messages.error(request, 'We could not verify your payment. Contact support if you were charged.')
        except Exception:
            logger.exception('Unexpected error verifying checkout session %s', session_id)
            messages.error(request, 'We could not verify your payment. Contact support if you were charged.')

    if course_id:
        if catalog_package_id:
            from catalog.models import Package
            pkg = Package.objects.filter(pk=catalog_package_id).only('course_packet_id').first()
            if pkg and pkg.course_packet_id:
                return redirect('packet_detail', course_id=int(course_id), packet_id=pkg.course_packet_id)
        return redirect('course_detail', course_id=course_id)
    if request.user.is_authenticated:
        return redirect('users:dashboard')
    return redirect('home')


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
        
        # Method 1: Get user from metadata / email / create guest account
        user, _ = resolve_checkout_user(session)
        payment_type = session.get('metadata', {}).get('payment_type')
        
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
                # One-time lifetime payment — only when explicitly tagged
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
            elif payment_type == 'catalog':
                fulfill_paid_session(session, user=user)
                logger.info('Catalog checkout completed for user %s', user.email)
            elif payment_type == 'course' or session.get('metadata', {}).get('course_id'):
                fulfill_paid_session(session, user=user)
                logger.info(f'Course checkout completed for user {user.email}')
            else:
                # Do NOT grant lifetime for unknown one-time payments
                profile.save()
                logger.warning(
                    'Checkout completed with unknown payment_type=%s mode=%s session=%s',
                    payment_type,
                    session.get('mode'),
                    session.get('id'),
                )
        else:
            logger.warning(f'Could not find/create user for checkout session: {session.get("id")}')
            # Guest course checkout with missing email is rare; still try payment row path
            if payment_type == 'course' or session.get('metadata', {}).get('course_id'):
                grant_course_access_from_session(session, user=None)
    
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


def checkout_subscription(request):
    """Site-wide subscription is disabled — students buy individual courses."""
    messages.info(
        request,
        'Subscriptions are not available yet. Please unlock the course you want from the Courses page.',
    )
    return redirect('courses')


def checkout_onetime(request):
    """Site-wide lifetime purchase is disabled — students buy individual courses."""
    messages.info(
        request,
        'Lifetime plans are not available yet. Please unlock the course you want from the Courses page.',
    )
    return redirect('courses')


def check_course_access(user, course):
    """True if user may watch paid videos for this course."""
    if not getattr(course, 'sell_as_packets', False):
        if getattr(course, 'price', None) is not None and course.price <= 0:
            return True
    if not getattr(user, 'is_authenticated', False):
        return False
    
    # Check premium access
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        if profile.has_premium_access():
            return True
    except Exception:
        pass
    
    # Check individual course access
    has_access = UserCourseAccess.objects.filter(
        user=user,
        course=course,
        is_active=True,
    ).exists()
    
    if has_access:
        return True
        
    # Check if there's a successful payment for this course
    # This handles cases where UserCourseAccess might not have been created properly
    successful_payment = Payment.objects.filter(
        user=user,
        course=course,
        status='succeeded'
    ).exists()
    
    if successful_payment:
        # Create missing access record
        try:
            payment = Payment.objects.filter(
                user=user,
                course=course,
                status='succeeded'
            ).first()
            UserCourseAccess.objects.get_or_create(
                user=user,
                course=course,
                defaults={'payment': payment, 'is_active': True}
            )
            return True
        except Exception:
            pass
    
    return False


def check_session_access(user, session, course=None):
    """True if the user may play this video (course purchase, catalog entitlement, or preview)."""
    if session is None:
        return False
    course = course or session.course or (session.level.course if session.level_id else None)
    if getattr(session, 'is_free_preview', False):
        return True
    if course is not None and check_course_access(user, course):
        return True
    from catalog.services.access import can_watch_session
    return can_watch_session(user, session)