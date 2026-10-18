from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def youtube_embed_url(url):
    """Convert YouTube URL to embed URL"""
    if not url:
        return None
    
    # Extract video ID from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            # Clean the video ID (remove any extra parameters)
            video_id = video_id.split('?')[0].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}?playsinline=1&rel=0"
    
    return None

@register.filter
def is_youtube_url(url):
    """Check if URL is a YouTube URL"""
    if not url:
        return False
    return 'youtube.com' in url or 'youtu.be' in url

@register.filter
def format_duration(seconds):
    """Format duration in seconds to MM:SS or HH:MM:SS"""
    if not seconds:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

@register.filter
def video_badge_class(video, user_purchased_videos=None):
    """Return CSS class for video badge based on access status"""
    if video.is_free:
        return "bg-green-500 text-white"
    elif user_purchased_videos and video.id in user_purchased_videos:
        return "bg-blue-500 text-white"
    else:
        return "bg-purple-500 text-white"

@register.filter
def video_badge_text(video, user_purchased_videos=None):
    """Return text for video badge based on access status"""
    if video.is_free:
        return "FREE"
    elif user_purchased_videos and video.id in user_purchased_videos:
        return "PURCHASED"
    else:
        return f"${video.price}"

@register.filter
def video_icon(video, user_purchased_videos=None):
    """Return icon for video based on access status"""
    if video.is_free:
        return "fas fa-play"
    elif user_purchased_videos and video.id in user_purchased_videos:
        return "fas fa-play"
    else:
        return "fas fa-lock"

@register.simple_tag
def breadcrumb_navigation(breadcrumbs):
    """Generate breadcrumb navigation HTML"""
    if not breadcrumbs:
        return ""
    
    html = '<nav class="flex" aria-label="Breadcrumb">'
    html += '<ol class="inline-flex items-center space-x-1 md:space-x-3">'
    
    for i, crumb in enumerate(breadcrumbs):
        if i == len(breadcrumbs) - 1:
            # Last item (current page)
            html += f'<li aria-current="page"><span class="text-gray-500">{crumb["name"]}</span></li>'
        else:
            # Link item
            html += f'<li class="inline-flex items-center">'
            if i > 0:
                html += '<svg class="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path></svg>'
            html += f'<a href="{crumb["url"]}" class="text-gray-700 hover:text-gray-900">{crumb["name"]}</a>'
            html += '</li>'
    
    html += '</ol></nav>'
    return mark_safe(html)





