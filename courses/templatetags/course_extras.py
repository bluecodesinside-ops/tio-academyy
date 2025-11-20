from django import template
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
            return f"https://www.youtube.com/embed/{video_id}"
    
    return None

@register.filter
def is_youtube_url(url):
    """Check if URL is a YouTube URL"""
    if not url:
        return False
    return 'youtube.com' in url or 'youtu.be' in url
