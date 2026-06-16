from urllib.parse import urlparse

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from courses.models import Course, Level, Session, UserProgress
from gallery.models import Photo, Video
from newsletter.models import NewsletterSubscription
from slideshow.models import SlideshowItem
from programs.models import DanceStyle
from payments.views import check_course_access


def _youtube_embed_origin(request):
    """YouTube iframe origin must match this page (scheme + host + port)."""
    p = urlparse(request.build_absolute_uri('/'))
    return f'{p.scheme}://{p.netloc}'


def home(request):
    """Homepage view with dynamic content"""
    embed_origin = _youtube_embed_origin(request)
    slideshow_youtube_slides = []
    for item in SlideshowItem.objects.filter(is_active=True).order_by('order', 'created_at'):
        if item.media_type != 'video' or not item.is_youtube_url():
            continue
        src = item.get_youtube_embed_src(embed_origin)
        if not src:
            continue
        item.youtube_embed_src = src
        slideshow_youtube_slides.append(item)

    context = {
        'featured_courses': Course.objects.filter(is_active=True)[:3],
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_levels': Level.objects.count(),
        'total_sessions': Session.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'slideshow_youtube_slides': slideshow_youtube_slides,
        'programs': DanceStyle.objects.filter(is_active=True).order_by('order', 'name')[:6],  # Show first 6 programs
    }
    return render(request, 'index.html', context)

def about(request):
    """About page view"""
    return render(request, 'about.html')


def course_detail(request, course_id):
    """Individual course detail view - First video is free preview, no login required to view course"""
    from users.models import UserProfile
    
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Get the first session (free preview)
    first_session = None
    if course.levels.exists():
        first_level = course.levels.first()
        if first_level.sessions.exists():
            first_session = first_level.sessions.first()
    
    # Check premium access for logged-in users
    has_premium_access = False
    user_progress = {}
    
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        has_premium_access = (
            profile.subscription_status == 'active' or 
            profile.has_lifetime_access
        )
        
        # Free courses are accessible to everyone
        if course.price == 0:
            has_premium_access = True
        
        # Get user progress
        for level in course.levels.all():
            for session in level.sessions.all():
                progress, created = UserProgress.objects.get_or_create(
                    user=request.user,
                    session=session,
                    defaults={'progress_percentage': 0}
                )
                user_progress[session.id] = progress
    else:
        # Free courses are accessible to everyone
        if course.price == 0:
            has_premium_access = True
    
    # Add user_progress and access info to each session
    for level in course.levels.all():
        for session in level.sessions.all():
            session.user_progress = user_progress.get(session.id) if request.user.is_authenticated else None
            # First session is always free (preview)
            session.is_free_preview = (session == first_session)
            # Other sessions require premium access
            session.requires_premium = (course.price > 0 and session != first_session)
            # Access: free preview OR (premium required AND has premium access)
            session.has_access = session.is_free_preview or (session.requires_premium and has_premium_access)
    
    # Get the first session as current_session for video display
    current_session = first_session
    
    context = {
        'course': course,
        'levels': course.levels.all(),
        'user_progress': user_progress,
        'has_premium_access': has_premium_access,
        'current_session': current_session,
        'first_session': first_session,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'course_detail.html', context)

def session_detail(request, session_id):
    """Individual session view with video player - First video is free preview, no login required for first video"""
    from users.models import UserProfile
    
    session = get_object_or_404(Session, id=session_id, is_active=True)
    course = session.level.course
    
    # Get the first session of the course (free preview)
    first_session = None
    if course.levels.exists():
        first_level = course.levels.first()
        if first_level.sessions.exists():
            first_session = first_level.sessions.first()
    
    # Check if this is the free preview session
    is_free_preview = (session == first_session)
    
    # Check premium access for logged-in users
    has_premium_access = False
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        has_premium_access = (
            profile.subscription_status == 'active' or 
            profile.has_lifetime_access
        )
    
    # Free courses are accessible to everyone
    if course.price == 0:
        has_premium_access = True
    
    # Check if user has access to this session
    has_access = is_free_preview or (course.price == 0) or has_premium_access
    
    # If no access, redirect to login or dashboard
    if not has_access:
        from django.contrib import messages
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to watch this video. The first video is free as a preview.')
            return redirect('users:login')
        else:
            messages.warning(request, 'This video requires premium access. The first video is free as a preview. Please subscribe or purchase lifetime access to watch all videos.')
            return redirect('users:dashboard')
    
    # Get or create user progress (only if logged in)
    progress = None
    if request.user.is_authenticated:
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            session=session,
            defaults={'progress_percentage': 0}
        )
    
    # Get next session for navigation
    next_session = None
    if progress:
        next_session = progress.get_next_session()
    
    # Check if next session requires premium
    next_requires_premium = False
    if next_session and course.price > 0:
        next_requires_premium = (next_session != first_session)
        if next_requires_premium and not has_premium_access:
            next_session = None  # Hide next button if they don't have access
    
    context = {
        'session': session,
        'course': course,
        'progress': progress,
        'next_session': next_session,
        'is_free_preview': is_free_preview,
        'has_premium_access': has_premium_access,
        'next_requires_premium': next_requires_premium,
    }
    return render(request, 'session_detail.html', context)

@login_required
def update_progress(request, session_id):
    """Update user progress for a session"""
    if request.method == 'POST':
        session = get_object_or_404(Session, id=session_id)
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            session=session
        )
        
        # Update progress data
        progress_percentage = int(request.POST.get('progress_percentage', 0))
        last_position = int(request.POST.get('last_position', 0))
        
        progress.progress_percentage = progress_percentage
        progress.last_watched_position = last_position
        progress.last_watched_at = timezone.now()
        
        # Mark as completed if progress is 90% or more
        if progress_percentage >= 90 and not progress.completed:
            progress.completed = True
            progress.completed_at = timezone.now()
        
        progress.save()
        
        return JsonResponse({
            'success': True,
            'completed': progress.completed,
            'progress_percentage': progress.progress_percentage
        })
    
    return JsonResponse({'success': False}, status=400)

def get_user_progress(request, course_id):
    """Get user progress for a course"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)
    
    course = get_object_or_404(Course, id=course_id)
    progress_data = {}
    
    for level in course.levels.all():
        level_progress = {
            'completed_sessions': 0,
            'total_sessions': level.sessions.count(),
            'sessions': {}
        }
        
        for session in level.sessions.all():
            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                session=session,
                defaults={'progress_percentage': 0}
            )
            
            level_progress['sessions'][session.id] = {
                'completed': progress.completed,
                'progress_percentage': progress.progress_percentage,
                'last_position': progress.last_watched_position
            }
            
            if progress.completed:
                level_progress['completed_sessions'] += 1
        
        progress_data[level.id] = level_progress
    
    return JsonResponse(progress_data)


def gallery(request):
    """Gallery page view with dynamic photos and videos"""
    context = {
        'photos': Photo.objects.filter(is_active=True),
        'videos': Video.objects.filter(is_active=True),
    }
    return render(request, 'gallery.html', context)

def courses(request):
    """Courses listing page"""
    courses_list = Course.objects.filter(is_active=True)
    context = {
        'courses': courses_list,
    }
    return render(request, 'courses.html', context)

def contact(request):
    """Contact page view"""
    return render(request, 'contact.html')

def faq(request):
    """FAQ page view"""
    return render(request, 'faq.html')

def privacy(request):
    """Privacy policy page view"""
    return render(request, 'privacy.html')

def terms(request):
    """Terms of service page view"""
    return render(request, 'terms.html')

def debug_video(request, session_id):
    """Debug view to test video display"""
    session = get_object_or_404(Session, id=session_id)
    return render(request, 'debug_video.html', {'session': session})
