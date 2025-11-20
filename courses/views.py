from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Course, Level, Session, UserProgress

def course_list(request):
    """API endpoint to get all courses"""
    courses = Course.objects.filter(is_active=True)
    data = []
    for course in courses:
        data.append({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'level': course.level,
            'duration': course.duration,
            'price': str(course.price),
            'rating': str(course.rating),
            'image_url': course.image.url if course.image else None,
        })
    return JsonResponse({'courses': data})

def course_detail(request, course_id):
    """API endpoint to get course details"""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    levels = course.levels.all()
    
    level_data = []
    for level in levels:
        sessions = level.sessions.filter(is_active=True)
        session_data = []
        for session in sessions:
            session_data.append({
                'id': session.id,
                'title': session.title,
                'description': session.description,
                'duration': session.duration,
                'video_url': session.video_url,
            })
        
        level_data.append({
            'id': level.id,
            'name': level.name,
            'description': level.description,
            'sessions': session_data,
        })
    
    data = {
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'level': course.level,
        'duration': course.duration,
        'price': str(course.price),
        'rating': str(course.rating),
        'image_url': course.image.url if course.image else None,
        'levels': level_data,
    }
    return JsonResponse(data)

def level_detail(request, course_id, level_id):
    """API endpoint to get level details"""
    level = get_object_or_404(Level, id=level_id, course_id=course_id)
    sessions = level.sessions.filter(is_active=True)
    
    session_data = []
    for session in sessions:
        session_data.append({
            'id': session.id,
            'title': session.title,
            'description': session.description,
            'duration': session.duration,
            'video_url': session.video_url,
        })
    
    data = {
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'course_title': level.course.title,
        'sessions': session_data,
    }
    return JsonResponse(data)

def session_detail(request, session_id):
    """API endpoint to get session details"""
    session = get_object_or_404(Session, id=session_id, is_active=True)
    
    data = {
        'id': session.id,
        'title': session.title,
        'description': session.description,
        'duration': session.duration,
        'video_url': session.video_url,
        'level_name': session.level.name,
        'course_title': session.level.course.title,
    }
    return JsonResponse(data)

@login_required
def user_progress(request):
    """API endpoint to get user progress"""
    if request.method == 'GET':
        progress = UserProgress.objects.filter(user=request.user)
        data = []
        for p in progress:
            data.append({
                'session_id': p.session.id,
                'session_title': p.session.title,
                'completed': p.completed,
                'progress_percentage': p.progress_percentage,
                'completed_at': p.completed_at.isoformat() if p.completed_at else None,
            })
        return JsonResponse({'progress': data})
    
    elif request.method == 'POST':
        # Update progress
        session_id = request.POST.get('session_id')
        progress_percentage = request.POST.get('progress_percentage', 0)
        completed = request.POST.get('completed', False)
        
        session = get_object_or_404(Session, id=session_id)
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            session=session
        )
        
        progress.progress_percentage = progress_percentage
        progress.completed = completed
        progress.save()
        
        return JsonResponse({'status': 'success'})
