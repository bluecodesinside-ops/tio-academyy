from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from courses.models import Course, Level, Session, UserProgress
from gallery.models import Photo, Video
from newsletter.models import NewsletterSubscription
from slideshow.models import SlideshowItem
from programs.models import DanceStyle

def home(request):
    """Homepage view with dynamic content"""
    context = {
        'featured_courses': Course.objects.filter(is_active=True)[:3],
        'total_courses': Course.objects.filter(is_active=True).count(),
        'total_levels': Level.objects.count(),
        'total_sessions': Session.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'slideshow_items': SlideshowItem.objects.filter(is_active=True).order_by('order', 'created_at'),
        'dance_styles': DanceStyle.objects.filter(is_active=True).order_by('order', 'name')[:6],  # Show first 6 styles
    }
    return render(request, 'index.html', context)

def about(request):
    """About page view"""
    return render(request, 'about.html')


def course_detail(request, course_id):
    """Individual course detail view with progress tracking"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Check if user has access to the course
    has_access = False
    if request.user.is_authenticated:
        has_access = check_course_access(request.user, course)
    elif course.price == 0:
        has_access = True  # Free courses are accessible to everyone
    
    # Get user progress if logged in and has access
    user_progress = {}
    if request.user.is_authenticated and has_access:
        for level in course.levels.all():
            for session in level.sessions.all():
                progress, created = UserProgress.objects.get_or_create(
                    user=request.user,
                    session=session,
                    defaults={'progress_percentage': 0}
                )
                user_progress[session.id] = progress
    
    # Add user_progress to each session for easier template access
    for level in course.levels.all():
        for session in level.sessions.all():
            session.user_progress = user_progress.get(session.id)
    
    # Get the first session as current_session for video display
    current_session = None
    if course.levels.exists():
        first_level = course.levels.first()
        if first_level.sessions.exists():
            current_session = first_level.sessions.first()
    
    context = {
        'course': course,
        'levels': course.levels.all(),
        'user_progress': user_progress,
        'has_access': has_access,
        'current_session': current_session,
    }
    return render(request, 'course_detail.html', context)

@login_required
def session_detail(request, session_id):
    """Individual session view with video player"""
    session = get_object_or_404(Session, id=session_id, is_active=True)
    
    # Get or create user progress
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        session=session,
        defaults={'progress_percentage': 0}
    )
    
    # Get next session for navigation
    next_session = progress.get_next_session()
    
    context = {
        'session': session,
        'progress': progress,
        'next_session': next_session,
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
