from urllib.parse import urlparse

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.conf import settings
from courses.models import Course, Level, Packet, Session, UserProgress
from gallery.models import Photo, Video
from newsletter.models import NewsletterSubscription
from slideshow.models import SlideshowItem
from payments.views import check_course_access, check_session_access


def _youtube_embed_origin(request):
    """YouTube iframe origin must match this page (scheme + host + port)."""
    p = urlparse(request.build_absolute_uri('/'))
    return f'{p.scheme}://{p.netloc}'


def home(request):
    """Homepage view with dynamic content"""
    from django.utils.translation import gettext as _

    embed_origin = _youtube_embed_origin(request)
    slideshow_slides = []
    for item in SlideshowItem.objects.filter(is_active=True).order_by('order', 'created_at'):
        slide = {
            'title': _(item.title) if item.title else '',
            'description': _(item.description) if item.description else '',
            'poster_url': item.video_thumbnail.url if item.video_thumbnail else None,
        }
        if item.media_type == 'video' and item.video_file:
            slide['slide_kind'] = 'video_file'
            slide['media_url'] = item.video_file.url
            if not slide['poster_url'] and item.image:
                slide['poster_url'] = item.image.url
        elif item.media_type == 'video' and item.is_youtube_url():
            src = item.get_youtube_embed_src(embed_origin)
            if not src:
                continue
            slide['slide_kind'] = 'youtube'
            slide['media_url'] = src
        elif item.media_type == 'image' and item.image:
            slide['slide_kind'] = 'image'
            slide['media_url'] = item.image.url
        else:
            continue
        slideshow_slides.append(slide)

    active_courses = Course.objects.filter(is_active=True).order_by('title')
    context = {
        'featured_courses': active_courses[:3],
        'total_courses': active_courses.count(),
        'total_levels': Level.objects.count(),
        'total_sessions': Session.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'slideshow_slides': slideshow_slides,
        # Unified catalog: homepage cards are Courses (not legacy DanceStyles)
        'programs': active_courses[:6],
    }
    return render(request, 'index.html', context)

def about(request):
    """About page view"""
    return render(request, 'about.html')


def _packet_catalog(packet):
    from django.core.exceptions import ObjectDoesNotExist
    try:
        linked = packet.catalog_package
        if linked:
            return linked
    except (ObjectDoesNotExist, AttributeError):
        pass
    from catalog.models import Package
    return (
        Package.objects.filter(course_packet=packet).first()
        or Package.objects.filter(
            product__linked_course_id=packet.course_id,
            title__iexact=packet.title,
        ).first()
        or Package.objects.filter(
            product__linked_course_id=packet.course_id,
            chapter_number=packet.order,
        ).first()
    )


def _has_course_unlock(request, course):
    if course.sell_as_packets:
        return bool(request.user.is_authenticated and check_course_access(request.user, course))
    if course.price == 0:
        return True
    return bool(request.user.is_authenticated and check_course_access(request.user, course))


def course_detail(request, course_id):
    """Course page: ordered videos; first is free preview; rest unlock after purchase/access."""
    course = get_object_or_404(Course, id=course_id, is_active=True)
    has_course_access = _has_course_unlock(request, course)
    sessions = []
    user_progress = {}
    first_session = None
    current_session = None
    preview_sessions = course.get_preview_sessions()
    preview_session = preview_sessions[0] if preview_sessions else None

    if not course.sell_as_packets:
        sessions = list(course.get_ordered_sessions().prefetch_related('catalog_assets'))
        if not sessions:
            sessions = list(
                Session.objects.filter(level__course=course, is_active=True).order_by('level__order', 'order', 'id')
            )

        first_session = preview_session
        if not first_session and sessions:
            first_session = sessions[0]

        if request.user.is_authenticated:
            for session in sessions:
                progress, created = UserProgress.objects.get_or_create(
                    user=request.user,
                    session=session,
                    defaults={'progress_percentage': 0},
                )
                user_progress[session.id] = progress

        for session in sessions:
            session.user_progress = user_progress.get(session.id) if request.user.is_authenticated else None
            is_preview = bool(session.is_free_preview)
            session.requires_premium = course.price > 0 and not is_preview
            session.has_access = (
                is_preview
                or has_course_access
                or course.price == 0
                or check_session_access(request.user, session, course)
            )

        current_session = first_session
        requested_id = request.GET.get('session')
        if requested_id:
            try:
                requested = next(s for s in sessions if s.id == int(requested_id))
                if requested.has_access:
                    current_session = requested
            except (StopIteration, ValueError, TypeError):
                pass

    from catalog.models import CourseProduct, ProductKind
    from catalog.services.access import can_watch_package

    catalog_product = CourseProduct.objects.filter(linked_course=course, is_active=True).first()
    catalog_packages = []
    catalog_assets = []
    catalog_tiers = []
    has_catalog_bundle = False
    packets = list(
        course.packets.filter(is_active=True).prefetch_related('videos').order_by('order', 'id')
    )
    if course.sell_as_packets and packets:
        if catalog_product is None:
            from catalog.services.sync import sync_course_packet
            synced = sync_course_packet(packets[0])
            catalog_product = synced.product if synced else None
        for packet in packets:
            cat = _packet_catalog(packet)
            packet.checkout_id = cat.id if cat else None
            packet.chapter_number = packet.order
            packet.has_catalog_access = has_course_access or (bool(cat) and can_watch_package(request.user, cat))
        catalog_packages = packets
        has_catalog_bundle = bool(catalog_packages) and all(p.has_catalog_access for p in catalog_packages)
        if preview_sessions:
            for session in preview_sessions:
                session.has_access = True
            current_session = preview_sessions[0]
            first_session = current_session
            requested_id = request.GET.get('preview') or request.GET.get('session')
            if requested_id:
                try:
                    requested = next(s for s in preview_sessions if s.id == int(requested_id))
                    current_session = requested
                except (StopIteration, ValueError, TypeError):
                    pass
    elif catalog_product:
        if catalog_product.kind == ProductKind.PHYSIO_PACKAGES:
            for package in catalog_product.active_packages().select_related('product__linked_course').prefetch_related('media_assets__session'):
                package.has_catalog_access = has_course_access or can_watch_package(request.user, package)
                catalog_packages.append(package)
            has_catalog_bundle = bool(catalog_packages) and all(p.has_catalog_access for p in catalog_packages)
        else:
            catalog_tiers = list(catalog_product.active_tiers())
            catalog_assets = list(
                catalog_product.media_assets.filter(is_active=True).select_related('session').order_by('order', 'id')
            )
            for asset in catalog_assets:
                session = asset.session
                asset.has_catalog_access = bool(
                    session and any(s.id == session.id and s.has_access for s in sessions)
                )

    has_any_catalog_access = (
        any(getattr(asset, 'has_catalog_access', False) for asset in catalog_assets)
        or any(getattr(package, 'has_catalog_access', False) for package in catalog_packages)
    )

    context = {
        'course': course,
        'sessions': sessions,
        'levels': course.levels.all(),
        'user_progress': user_progress,
        'has_course_access': has_course_access,
        'has_premium_access': has_course_access,
        'current_session': current_session,
        'first_session': first_session,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'catalog_product': catalog_product,
        'catalog_packages': catalog_packages,
        'catalog_assets': catalog_assets,
        'catalog_tiers': catalog_tiers,
        'has_catalog_bundle': has_catalog_bundle,
        'has_any_catalog_access': has_any_catalog_access,
        'has_free_preview': bool(preview_sessions),
        'preview_sessions': preview_sessions,
    }
    return render(request, 'course_detail.html', context)


def packet_detail(request, course_id, packet_id):
    """One packet: its videos, then buy that packet."""
    from catalog.services.access import can_watch_package
    from catalog.services.sync import sync_course_packet

    course = get_object_or_404(Course, id=course_id, is_active=True)
    packet = get_object_or_404(
        Packet.objects.select_related('course', 'catalog_package'),
        id=packet_id,
        course=course,
        is_active=True,
    )
    videos = list(packet.videos.filter(is_active=True).order_by('order', 'id'))
    has_course_access = _has_course_unlock(request, course)
    catalog_package = _packet_catalog(packet) or sync_course_packet(packet)
    has_packet_access = has_course_access or (
        bool(catalog_package) and can_watch_package(request.user, catalog_package)
    )

    user_progress = {}
    if request.user.is_authenticated and has_packet_access:
        for session in videos:
            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                session=session,
                defaults={'progress_percentage': 0},
            )
            user_progress[session.id] = progress

    for session in videos:
        session.user_progress = user_progress.get(session.id)
        session.has_access = (
            has_packet_access
            or bool(session.is_free_preview)
            or check_session_access(request.user, session, course)
        )

    current_session = None
    playable = [s for s in videos if s.has_access]
    if playable:
        current_session = next((s for s in playable if s.is_free_preview), playable[0])
        if has_packet_access:
            current_session = playable[0]
        requested_id = request.GET.get('session')
        if requested_id:
            try:
                requested = next(s for s in videos if s.id == int(requested_id))
                if requested.has_access:
                    current_session = requested
            except (StopIteration, ValueError, TypeError):
                pass

    return render(request, 'packet_detail.html', {
        'course': course,
        'packet': packet,
        'sessions': videos,
        'current_session': current_session,
        'has_packet_access': has_packet_access,
        'has_premium_access': has_packet_access,
        'checkout_id': catalog_package.id if catalog_package else None,
    })

def session_detail(request, session_id):
    """Watch a single video. Free preview is open; other videos need purchase/subscription."""
    from django.contrib import messages
    from django.utils.translation import gettext as gettext

    session = get_object_or_404(Session, id=session_id, is_active=True)
    course = session.course or (session.level.course if session.level_id else None)
    if not course:
        messages.error(request, gettext('This video is not linked to a course.'))
        return redirect('courses')

    is_free_preview = bool(session.is_free_preview)

    has_course_access = _has_course_unlock(request, course)
    has_access = is_free_preview or has_course_access or check_session_access(request.user, session, course)

    if not has_access:
        if session.packet_id and course.sell_as_packets:
            messages.warning(request, gettext('Buy this packet to unlock these videos.'))
            return redirect('packet_detail', course_id=course.id, packet_id=session.packet_id)
        messages.warning(
            request,
            gettext('This video unlocks after purchasing the course (or with an active subscription / lifetime access). The first video is free as a preview.'),
        )
        return redirect('course_detail', course_id=course.id)

    progress = None
    if request.user.is_authenticated:
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            session=session,
            defaults={'progress_percentage': 0},
        )

    if session.packet_id:
        next_session = (
            Session.objects.filter(packet_id=session.packet_id, is_active=True, order__gt=session.order)
            .order_by('order', 'id')
            .first()
        )
        if next_session and not check_session_access(request.user, next_session, course):
            next_session = None
        next_requires_premium = False
    else:
        next_session = progress.get_next_session() if progress else (
            Session.objects.filter(course=course, is_active=True, order__gt=session.order)
            .order_by('order', 'id')
            .first()
        )
        next_requires_premium = False
        if next_session and course.price > 0:
            next_is_preview = bool(next_session.is_free_preview)
            next_requires_premium = not next_is_preview
            if next_requires_premium and not has_course_access:
                next_session = None

    context = {
        'session': session,
        'course': course,
        'progress': progress,
        'next_session': next_session,
        'is_free_preview': is_free_preview,
        'has_course_access': has_course_access,
        'has_premium_access': has_course_access,
        'next_requires_premium': next_requires_premium,
    }
    return render(request, 'session_detail.html', context)


def watch_session(request, session_id):
    """Open the real player. Phones cannot play Bunny inside our page iframe."""
    session = get_object_or_404(Session, id=session_id, is_active=True)
    course = session.course or (session.level.course if session.level_id else None)
    if not course:
        return redirect('courses')

    is_free_preview = bool(session.is_free_preview)
    has_access = (
        is_free_preview
        or _has_course_unlock(request, course)
        or check_session_access(request.user, session, course)
    )
    if not has_access:
        if session.packet_id and course.sell_as_packets:
            return redirect('packet_detail', course_id=course.id, packet_id=session.packet_id)
        return redirect('course_detail', course_id=course.id)

    play_url = session.get_bunny_play_url()
    if play_url:
        return redirect(play_url)
    if session.is_youtube_url() and session.video_url:
        return redirect(session.video_url)
    return redirect('session_detail', session_id=session.id)

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
    from catalog.models import CourseProduct
    courses_list = list(Course.objects.filter(is_active=True))
    package_course_ids = set(
        CourseProduct.objects.filter(
            linked_course_id__isnull=False,
            is_active=True,
            kind='physio_packages',
        ).values_list('linked_course_id', flat=True)
    )
    for course in courses_list:
        course.sold_as_packages = bool(course.sell_as_packets or course.id in package_course_ids)
        packet_prices = [
            p for p in course.packets.filter(is_active=True).values_list('price', flat=True) if p
        ]
        course.from_price = min(packet_prices) if packet_prices else None
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
