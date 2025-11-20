from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.db.models import Q
from django.utils import timezone
from .models import DanceStyle, Category, SkillLevel, Video, UserVideoAccess
from pricing.models import Subscription


def check_video_access(user, video):
    """
    Check if user has access to a video based on their subscription
    Returns: (has_access, access_type, upgrade_required)
    """
    # Free videos are accessible to everyone
    if video.is_free:
        return True, 'free', False
    
    # Check if user is authenticated
    if not user.is_authenticated:
        return False, 'login_required', True
    
    # Check if user has active subscription
    try:
        subscription = Subscription.objects.filter(
            user=user,
            status__in=['active', 'trialing']
        ).latest('created_at')
    except Subscription.DoesNotExist:
        return False, 'subscription_required', True
    
    # Check if subscription package allows access to this video's skill level
    package = subscription.package
    allowed_levels = {
        'standard': ['basic'],
        'pro': ['basic', 'intermediate'],
        'gold': ['basic', 'intermediate', 'advanced'],
    }.get(package.tier, [])
    
    if video.skill_level.level in allowed_levels:
        return True, 'subscription', False
    else:
        return False, 'upgrade_required', True


def explore_programs(request):
    """Level 1: Display all dance styles in a grid layout"""
    dance_styles = DanceStyle.objects.filter(is_active=True).order_by('order', 'name')
    
    context = {
        'dance_styles': dance_styles,
        'page_title': 'Explore Dance Programs',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Explore Programs', 'url': None}
        ]
    }
    return render(request, 'programs/explore_programs.html', context)


def dance_style_detail(request, style_slug):
    """Level 2: Display categories for a specific dance style"""
    dance_style = get_object_or_404(DanceStyle, slug=style_slug, is_active=True)
    categories = Category.objects.filter(
        dance_style=dance_style, 
        is_active=True
    ).order_by('order', 'name')
    
    context = {
        'dance_style': dance_style,
        'categories': categories,
        'page_title': f'{dance_style.name} Programs',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Explore Programs', 'url': '/explore-programs/'},
            {'name': dance_style.name, 'url': None}
        ]
    }
    return render(request, 'programs/dance_style_detail.html', context)


def category_detail(request, style_slug, category_slug):
    """Level 3: Display skill levels for a specific category"""
    dance_style = get_object_or_404(DanceStyle, slug=style_slug, is_active=True)
    category = get_object_or_404(
        Category, 
        slug=category_slug, 
        dance_style=dance_style, 
        is_active=True
    )
    skill_levels = SkillLevel.objects.filter(
        category=category, 
        is_active=True
    ).order_by('order', 'level')
    
    context = {
        'dance_style': dance_style,
        'category': category,
        'skill_levels': skill_levels,
        'page_title': f'{category.name} - {dance_style.name}',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Explore Programs', 'url': '/explore-programs/'},
            {'name': dance_style.name, 'url': f'/explore-programs/{style_slug}/'},
            {'name': category.name, 'url': None}
        ]
    }
    return render(request, 'programs/category_detail.html', context)


def skill_level_detail(request, style_slug, category_slug, level):
    """Level 4: Display videos for a specific skill level"""
    dance_style = get_object_or_404(DanceStyle, slug=style_slug, is_active=True)
    category = get_object_or_404(
        Category, 
        slug=category_slug, 
        dance_style=dance_style, 
        is_active=True
    )
    skill_level = get_object_or_404(
        SkillLevel, 
        category=category, 
        level=level, 
        is_active=True
    )
    videos = Video.objects.filter(
        skill_level=skill_level, 
        is_active=True
    ).order_by('order', 'title')
    
    # Determine if user has access to each video using subscription system
    for video in videos:
        has_access, access_type, upgrade_required = check_video_access(request.user, video)
        video.has_access = has_access
        video.access_type = access_type
        video.upgrade_required = upgrade_required
    
    context = {
        'dance_style': dance_style,
        'category': category,
        'skill_level': skill_level,
        'videos': videos,
        'page_title': f'{skill_level.get_level_display()} {category.name} - {dance_style.name}',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Explore Programs', 'url': '/explore-programs/'},
            {'name': dance_style.name, 'url': f'/explore-programs/{style_slug}/'},
            {'name': category.name, 'url': f'/explore-programs/{style_slug}/{category_slug}/'},
            {'name': skill_level.get_level_display(), 'url': None}
        ]
    }
    return render(request, 'programs/skill_level_detail.html', context)


def video_detail(request, style_slug, category_slug, level, video_slug):
    """Video player page with access control"""
    dance_style = get_object_or_404(DanceStyle, slug=style_slug, is_active=True)
    category = get_object_or_404(
        Category, 
        slug=category_slug, 
        dance_style=dance_style, 
        is_active=True
    )
    skill_level = get_object_or_404(
        SkillLevel, 
        category=category, 
        level=level, 
        is_active=True
    )
    video = get_object_or_404(
        Video, 
        skill_level=skill_level, 
        slug=video_slug, 
        is_active=True
    )
    
    # Check if user has access to this video using subscription system
    has_access, access_type, upgrade_required = check_video_access(request.user, video)
    
    if not has_access:
        if access_type == 'login_required':
            messages.warning(request, 'Please log in to access this video.')
            return redirect('admin:login')
        elif access_type == 'subscription_required':
            messages.warning(request, 'You need a subscription to access this video. Please choose a plan.')
            return redirect('pricing:pricing_page')
        elif access_type == 'upgrade_required':
            messages.warning(request, 'You need to upgrade your subscription to access this video.')
            return redirect('pricing:pricing_page')
        else:
            messages.warning(request, 'Access denied. Please contact support.')
            return redirect('programs:skill_level_detail', 
                           style_slug=style_slug, 
                           category_slug=category_slug, 
                           level=level)
    
    # Increment view count if user has access
    if has_access:
        video.increment_view_count()
    
    # Get related videos (other videos in the same skill level)
    related_videos = Video.objects.filter(
        skill_level=skill_level,
        is_active=True
    ).exclude(id=video.id).order_by('order', 'title')[:6]
    
    # Get user's purchased videos for related videos
    user_purchased_videos = set()
    if request.user.is_authenticated and related_videos:
        user_purchased_videos = set(
            UserVideoAccess.objects.filter(
                user=request.user,
                video__in=related_videos
            ).values_list('video_id', flat=True)
        )
    
    context = {
        'dance_style': dance_style,
        'category': category,
        'skill_level': skill_level,
        'video': video,
        'has_access': has_access,
        'related_videos': related_videos,
        'user_purchased_videos': user_purchased_videos,
        'page_title': f'{video.title} - {skill_level.get_level_display()} {category.name}',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Explore Programs', 'url': '/explore-programs/'},
            {'name': dance_style.name, 'url': f'/explore-programs/{style_slug}/'},
            {'name': category.name, 'url': f'/explore-programs/{style_slug}/{category_slug}/'},
            {'name': skill_level.get_level_display(), 'url': f'/explore-programs/{style_slug}/{category_slug}/{level}/'},
            {'name': video.title, 'url': None}
        ]
    }
    return render(request, 'programs/video_detail.html', context)


@login_required
def purchase_video(request, video_id):
    """Handle video purchase (placeholder for future Stripe integration)"""
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    if video.is_free:
        messages.info(request, "This video is already free!")
        return redirect(video.get_absolute_url())
    
    # Check if user already has access
    if UserVideoAccess.objects.filter(user=request.user, video=video).exists():
        messages.info(request, "You already have access to this video!")
        return redirect(video.get_absolute_url())
    
    # For now, just create a free access record (in real implementation, integrate with Stripe)
    UserVideoAccess.objects.create(
        user=request.user,
        video=video,
        payment_id=f"demo_{timezone.now().timestamp()}"
    )
    
    messages.success(request, f"Successfully purchased access to '{video.title}'!")
    return redirect(video.get_absolute_url())


def search_programs(request):
    """Search across all programs"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        # Search in dance styles
        dance_styles = DanceStyle.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:5]
        
        # Search in categories
        categories = Category.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:5]
        
        # Search in videos
        videos = Video.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_active=True
        )[:10]
        
        results = {
            'dance_styles': dance_styles,
            'categories': categories,
            'videos': videos,
        }
    
    context = {
        'query': query,
        'results': results,
        'page_title': f'Search Results for "{query}"' if query else 'Search Programs',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Explore Programs', 'url': '/explore-programs/'},
            {'name': 'Search', 'url': None}
        ]
    }
    return render(request, 'programs/search.html', context)