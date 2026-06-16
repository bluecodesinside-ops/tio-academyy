from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import UserProfile
from courses.models import Course
import stripe
from django.conf import settings


def register_view(request):
    """User registration page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if not all([email, password, password_confirm]):
            messages.error(request, 'All fields are required')
            return render(request, 'users/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'users/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'users/register.html')
        
        try:
            # Use email as username (or create unique username)
            username = email.split('@')[0]
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{email.split('@')[0]}{counter}"
                counter += 1
            
            user = User.objects.create_user(username=username, email=email, password=password)
            # UserProfile is created automatically via signal
            # Auto-login and redirect to dashboard
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('users:dashboard')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'users/register.html')
    
    return render(request, 'users/register.html')


def login_view(request):
    """User login page"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not all([email, password]):
            messages.error(request, 'Email and password are required')
            return render(request, 'users/login.html')
        
        # Try to find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            return render(request, 'users/login.html')
        
        # Authenticate user
        user = authenticate(request, username=user.username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to 'next' parameter if provided, otherwise dashboard
            next_url = request.POST.get('next') or request.GET.get('next', 'users:dashboard')
            # Validate next_url to prevent open redirects
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            elif next_url and ':' in next_url:
                # It's a URL name, use redirect
                return redirect(next_url)
            else:
                return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid email or password')
            return render(request, 'users/login.html')
    
    return render(request, 'users/login.html')


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('home')


@login_required
def dashboard(request):
    """User dashboard showing course access, videos, and materials"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    courses = Course.objects.filter(is_active=True)
    
    # Check if payment was just completed
    session_id = request.GET.get('session_id')
    if session_id:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                messages.success(request, 'Payment successful! Your access has been activated.')
        except:
            pass
    
    # Import UserProgress to check completion
    from courses.models import UserProgress, Session
    
    # Check access for each course and get sessions/videos
    course_access = []
    for course in courses:
        has_access = (
            profile.subscription_status == 'active' or 
            profile.has_lifetime_access or
            course.price == 0  # Free courses
        )
        
        # Get all sessions for this course
        sessions = []
        for level in course.levels.all():
            for session in level.sessions.filter(is_active=True):
                # Check if user has progress for this session
                try:
                    progress = UserProgress.objects.get(user=request.user, session=session)
                    is_completed = progress.completed
                    progress_percentage = progress.progress_percentage
                except UserProgress.DoesNotExist:
                    is_completed = False
                    progress_percentage = 0
                
                # Determine if session is accessible
                # First session is always free preview
                first_session = level.sessions.filter(is_active=True).order_by('order').first()
                is_free_preview = (session == first_session)
                session_has_access = has_access or is_free_preview or (course.price == 0)
                
                sessions.append({
                    'session': session,
                    'level': level,
                    'is_completed': is_completed,
                    'progress_percentage': progress_percentage,
                    'has_access': session_has_access,
                    'is_free_preview': is_free_preview,
                    'video_url': session.video_file.url if session.video_file else session.video_url,
                    'has_video': bool(session.video_file or session.video_url),
                })
        
        # Calculate course progress
        total_sessions = len(sessions)
        completed_sessions = sum(1 for s in sessions if s['is_completed'])
        course_progress = int((completed_sessions / total_sessions * 100)) if total_sessions > 0 else 0
        
        course_access.append({
            'course': course,
            'has_access': has_access,
            'sessions': sessions,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'course_progress': course_progress,
        })
    
    context = {
        'user': request.user,
        'profile': profile,
        'course_access': course_access,
        'has_premium_access': profile.has_premium_access(),
    }
    return render(request, 'users/dashboard.html', context)


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
