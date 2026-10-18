from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Course, Level, Session, UserProgress
from payments.views import check_course_access, check_session_access


def _can_see_playback(user, course, session=None):
    """True only when playback URLs may leave the server."""
    if session is not None:
        return check_session_access(user, session, course)
    return check_course_access(user, course)


def _session_public_payload(user, course, session):
    """Session metadata for APIs — omit video URLs unless caller has access."""
    allowed = _can_see_playback(user, course, session)
    data = {
        'id': session.id,
        'title': session.title,
        'description': session.description,
        'duration': session.duration,
        'order': getattr(session, 'order', None),
        'is_free_preview': session.is_free_preview,
        'locked': not allowed,
    }
    if allowed:
        data['video_url'] = session.video_url
        data['playback_kind'] = session.get_playback_kind()
    else:
        data['video_url'] = None
        data['playback_kind'] = None
    return data


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
    """API endpoint to get course details (playback URLs gated by access)."""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    sessions = course.get_ordered_sessions()
    session_data = [
        _session_public_payload(request.user, course, session)
        for session in sessions
    ]

    data = {
        'id': course.id,
        'title': course.title,
        'description': course.description,
        'level': course.level,
        'duration': course.duration,
        'price': str(course.price),
        'rating': str(course.rating),
        'image_url': course.image.url if course.image else None,
        'sessions': session_data,
    }
    return JsonResponse(data)


def level_detail(request, course_id, level_id):
    """API endpoint to get level details (playback URLs gated by access)."""
    level = get_object_or_404(Level, id=level_id, course_id=course_id)
    course = level.course
    sessions = level.sessions.filter(is_active=True)

    session_data = [
        _session_public_payload(request.user, course, session)
        for session in sessions
    ]

    data = {
        'id': level.id,
        'name': level.name,
        'description': level.description,
        'course_title': course.title,
        'sessions': session_data,
    }
    return JsonResponse(data)


def session_detail(request, session_id):
    """API endpoint to get session details (playback URL gated by access)."""
    session = get_object_or_404(Session, id=session_id, is_active=True)
    course = session.course or (session.level.course if session.level_id else None)
    if course is None:
        return JsonResponse({'error': 'Session has no course'}, status=404)

    payload = _session_public_payload(request.user, course, session)
    payload['level_name'] = session.level.name if session.level_id else None
    payload['course_title'] = course.title
    return JsonResponse(payload)


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
