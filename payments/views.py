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

# Set Stripe API key
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
    """Handle successful payment"""
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'No session ID provided')
        return redirect('courses')
    
    try:
        # Retrieve the checkout session
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Get the payment record
        payment = Payment.objects.get(stripe_session_id=session_id)
        
        if session.payment_status == 'paid':
            # Update payment status
            payment.status = 'succeeded'
            payment.save()
            
            # Grant course access
            UserCourseAccess.objects.create(
                user=payment.user,
                course=payment.course,
                payment=payment
            )
            
            messages.success(request, f'Payment successful! You now have access to {payment.course.title}')
            return redirect('course_detail', course_id=payment.course.id)
        else:
            messages.error(request, 'Payment was not completed')
            return redirect('courses')
            
    except Payment.DoesNotExist:
        messages.error(request, 'Payment record not found')
        return redirect('courses')
    except stripe.error.StripeError as e:
        messages.error(request, f'Stripe error: {str(e)}')
        return redirect('courses')


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks for payment confirmation"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
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
                    
        except Payment.DoesNotExist:
            pass
    
    return HttpResponse(status=200)


def check_course_access(user, course):
    """Check if user has access to a course"""
    return UserCourseAccess.objects.filter(
        user=user, 
        course=course, 
        is_active=True
    ).exists()