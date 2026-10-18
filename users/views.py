from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import UserProfile
from courses.models import Course
import stripe
from django.conf import settings


def _library_item(title, url, cover_url='', subtitle=''):
    return {
        'title': title,
        'subtitle': subtitle,
        'cover_url': cover_url or '',
        'url': url,
    }


def _build_library(user, profile, purchases):
    library = []
    seen_packets = set()
    seen_courses = set()

    for purchase in purchases:
        packet = getattr(purchase.package, 'course_packet', None) if purchase.package_id else None
        if packet and packet.pk not in seen_packets:
            seen_packets.add(packet.pk)
            library.append(_library_item(
                packet.title,
                reverse('packet_detail', args=[packet.course_id, packet.pk]),
                packet.get_cover_url(),
                packet.course.title if packet.course_id else '',
            ))
            continue
        course = getattr(purchase.product, 'linked_course', None) if purchase.product_id else None
        if course and not course.sell_as_packets and course.pk not in seen_courses:
            seen_courses.add(course.pk)
            library.append(_library_item(
                course.title,
                reverse('course_detail', args=[course.pk]),
                course.image.url if course.image else '',
            ))

    from payments.models import UserCourseAccess
    for access in UserCourseAccess.objects.filter(
        user=user, is_active=True
    ).select_related('course'):
        course = access.course
        if not course or course.pk in seen_courses or course.sell_as_packets:
            continue
        seen_courses.add(course.pk)
        library.append(_library_item(
            course.title,
            reverse('course_detail', args=[course.pk]),
            course.image.url if course.image else '',
        ))

    if profile.has_premium_access():
        for course in Course.objects.filter(is_active=True, sell_as_packets=False):
            if course.pk in seen_courses:
                continue
            seen_courses.add(course.pk)
            library.append(_library_item(
                course.title,
                reverse('course_detail', args=[course.pk]),
                course.image.url if course.image else '',
            ))
    return library


def _safe_next(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if isinstance(next_url, str) and next_url.startswith('/'):
        return next_url
    return ''


def register_view(request):
    """Create an account to enroll and watch courses."""
    if request.user.is_authenticated:
        return redirect(_safe_next(request) or 'users:dashboard')

    next_url = _safe_next(request)
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if not all([email, password, password_confirm]):
            messages.error(request, _('All fields are required'))
            return render(request, 'users/register.html', {'next_url': next_url})

        if password != password_confirm:
            messages.error(request, _('Passwords do not match'))
            return render(request, 'users/register.html', {'next_url': next_url})

        if User.objects.filter(email=email).exists():
            messages.error(request, _('Email already registered'))
            return render(request, 'users/register.html', {'next_url': next_url})

        try:
            username = email.split('@')[0]
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{email.split('@')[0]}{counter}"
                counter += 1

            user = User.objects.create_user(username=username, email=email, password=password)
            # Ensure profile exists before login
            from .models import UserProfile
            UserProfile.objects.get_or_create(user=user)
            
            login(request, user)
            messages.success(request, _('Account created. You can enroll and watch courses.'))
            return redirect(next_url or 'users:dashboard')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'users/register.html', {'next_url': next_url})

    return render(request, 'users/register.html', {'next_url': next_url})


def login_view(request):
    """Sign in with email and password."""
    if request.user.is_authenticated:
        return redirect(_safe_next(request) or 'users:dashboard')

    next_url = _safe_next(request)
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        password = request.POST.get('password')

        if not all([email, password]):
            messages.error(request, _('Email and password are required'))
            return render(request, 'users/login.html', {'next_url': next_url})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, _('Invalid email or password'))
            return render(request, 'users/login.html', {'next_url': next_url})

        user = authenticate(request, username=user.username, password=password)
        if user is not None:
            login(request, user)
            try:
                from payments.views import sync_paid_access_for_user
                sync_paid_access_for_user(user)
            except Exception:
                pass
            posted_next = request.POST.get('next') or next_url
            if posted_next and str(posted_next).startswith('/'):
                return redirect(posted_next)
            return redirect('users:dashboard')
        messages.error(request, _('Invalid email or password'))
        return render(request, 'users/login.html', {'next_url': next_url})

    return render(request, 'users/login.html', {'next_url': next_url})


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, _('You have been logged out'))
    return redirect('home')


@login_required
def dashboard(request):
    """After purchase, students see only the courses/packets they own."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    try:
        from payments.views import sync_paid_access_for_user
        sync_paid_access_for_user(request.user)
    except Exception:
        pass

    session_id = request.GET.get('session_id')
    if session_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                messages.success(request, _('Payment successful! Your access has been activated.'))
                return redirect('users:dashboard')
        except Exception:
            pass

    from catalog.services.access import active_entitlements_qs
    purchases = list(
        active_entitlements_qs(request.user).select_related(
            'package',
            'package__course_packet',
            'package__course_packet__course',
            'product',
            'product__linked_course',
        )
    )
    library = _build_library(request.user, profile, purchases)

    return render(request, 'users/dashboard.html', {
        'user': request.user,
        'profile': profile,
        'library': library,
        'has_active_purchase': bool(library),
    })


@login_required
def user_profile(request):
    """Get user profile information (API)"""
    user = request.user
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'date_joined': user.date_joined.isoformat(),
    }
    return JsonResponse(data)


_PIXEL = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00'
    b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


def stats_hit(request):
    """Invisible beacon from the public site. Counts one visit per page."""
    from django.http import HttpResponse
    from users.stats import record_visit
    record_visit(request)
    response = HttpResponse(_PIXEL, content_type='image/gif')
    response['Cache-Control'] = 'no-store, no-cache'
    return response
