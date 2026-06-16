from urllib.parse import urlparse

from django.http import JsonResponse
from .models import SlideshowItem


def _embed_origin(request):
    p = urlparse(request.build_absolute_uri('/'))
    return f'{p.scheme}://{p.netloc}'


def slideshow_data(request):
    """API endpoint to get slideshow data as JSON"""
    items = SlideshowItem.objects.filter(is_active=True).order_by('order', 'created_at')
    origin = _embed_origin(request)

    slideshow_data = []
    for item in items:
        slide_data = {
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'media_type': item.media_type,
            'media_url': item.get_media_url(),
            'thumbnail_url': item.get_thumbnail_url(),
            'is_youtube': item.is_youtube_url(),
            'youtube_embed_url': item.get_youtube_embed_url(),
            'youtube_embed_src': item.get_youtube_embed_src(origin),
        }
        slideshow_data.append(slide_data)
    
    return JsonResponse({
        'items': slideshow_data,
        'total': len(slideshow_data)
    })