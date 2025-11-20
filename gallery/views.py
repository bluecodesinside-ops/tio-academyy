from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db import models
from .models import Photo, Video, Location, MediaType
from .forms import MediaUploadForm
from django.conf import settings
import requests

def gallery_view(request):
    # Read selected location from query param; default to 'all'
    current_location = request.GET.get('location', 'all')
    print(f"DEBUG: Current location filter: {current_location}")

    # Base querysets - only get photos that have either an image or image_url
    photos_qs = Photo.objects.filter(
        is_active=True
    ).exclude(
        image='',  # Exclude empty image fields
        image_url=''  # Exclude empty image_url fields
    ).order_by('-created_at')
    
    # Get videos that have either video_file or video_url
    from django.db.models import Q
    videos_qs = Video.objects.filter(
        is_active=True
    ).filter(
        Q(video_file__isnull=False) | Q(video_url__isnull=False)
    ).order_by('-created_at')
    
    print(f"DEBUG: Found {photos_qs.count()} active photos in total")
    print(f"DEBUG: Found {videos_qs.count()} active videos in total")
    
    # Debug: Print first few photos
    for i, photo in enumerate(photos_qs[:3], 1):
        has_image = bool(photo.image and hasattr(photo.image, 'storage') and photo.image.storage.exists(photo.image.name))
        print(f"DEBUG: Photo {i}: ID={photo.id}, Title={photo.title}, Has image={has_image}, Image URL={photo.image_url or 'N/A'}")
    
    # Debug: Print first few videos
    for i, video in enumerate(videos_qs[:3], 1):
        has_video_file = bool(video.video_file)
        print(f"DEBUG: Video {i}: ID={video.id}, Title={video.title}, Has video file={has_video_file}, Video URL={video.video_url or 'N/A'}")

    # Apply server-side filtering when a specific location is selected
    if current_location and current_location != 'all':
        photos_qs = photos_qs.filter(location=current_location)
        videos_qs = videos_qs.filter(location=current_location)
        print(f"DEBUG: After location filter, {photos_qs.count()} photos remain")

    # Get all available locations for filtering (list of dicts for template)
    locations = [
        {'name': location.value, 'slug': location.name.lower(), 'value': location.name}
        for location in Location
    ]

    # Pagination for photos - 10 photos per page
    photo_paginator = Paginator(photos_qs, 10)  # 10 photos per page
    photo_page_number = request.GET.get('photo_page', 1)
    photo_page_obj = photo_paginator.get_page(photo_page_number)

    # Pagination for videos - 10 videos per page
    video_paginator = Paginator(videos_qs, 10)  # 10 videos per page
    video_page_number = request.GET.get('video_page', 1)
    video_page_obj = video_paginator.get_page(video_page_number)

    return render(request, 'gallery.html', {
        'photos': photo_page_obj,
        'videos': video_page_obj,
        'locations': locations,
        'current_location': current_location,
        'MEDIA_URL': settings.MEDIA_URL
    })

def gallery_cassia_view(request):
    photos = Photo.objects.filter(is_active=True)
    videos = Video.objects.filter(is_active=True)
    locations = [location.value for location in Location]
    return render(request, 'gallery_cassia.html', {
        'photos': photos,
        'videos': videos,
        'locations': locations,
        'MEDIA_URL': settings.MEDIA_URL
    })

def upload_media(request):
    if request.method == 'POST':
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.cleaned_data['category']
            media_type = form.cleaned_data['media_type']
            upload_method = form.cleaned_data['upload_method']
            media_files = request.FILES.getlist('media_files')
            media_url = form.cleaned_data.get('media_url')
            
            created_count = 0
            
            if upload_method == 'file' and media_files:
                # Handle multiple file uploads
                for media_file in media_files:
                    if media_type == MediaType.PHOTO.name:
                        Photo.objects.create(
                            location=category,
                            media_type=media_type,
                            image=media_file,
                            is_active=True
                        )
                    elif media_type == MediaType.VIDEO.name:
                        Video.objects.create(
                            location=category,
                            media_type=media_type,
                            video_file=media_file,
                            is_active=True
                        )
                    created_count += 1
                    
            elif upload_method == 'url' and media_url:
                # Handle single URL upload
                if media_type == MediaType.PHOTO.name:
                    Photo.objects.create(
                        location=category,
                        media_type=media_type,
                        image_url=media_url,
                        is_active=True
                    )
                elif media_type == MediaType.VIDEO.name:
                    Video.objects.create(
                        location=category,
                        media_type=media_type,
                        video_url=media_url,
                        is_active=True
                    )
                created_count = 1
            
            messages.success(request, f'Successfully uploaded {created_count} {media_type.lower()}(s)!')
            return redirect('gallery:gallery')
    else:
        form = MediaUploadForm()
    return render(request, 'upload_media.html', {'form': form})


def download_image(request):
    """
    Enhanced proxy endpoint to download images from any URL with improved error handling
    """
    try:
        image_url = request.GET.get('url')
        filename = request.GET.get('filename', 'image.jpg')
        
        if not image_url:
            return JsonResponse({'error': 'No image URL provided'}, status=400)
        
        # Security: Validate the URL
        from urllib.parse import urlparse
        parsed_url = urlparse(image_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return JsonResponse({'error': 'Invalid URL'}, status=400)
            
        # Handle local files (if needed)
        if image_url.startswith(settings.MEDIA_URL):
            import os
            file_path = os.path.join(settings.MEDIA_ROOT, image_url.replace(settings.MEDIA_URL, ''))
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='image/jpeg')
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response
        
        # Handle external URLs
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Referer': request.META.get('HTTP_REFERER', ''),
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Stream the file to avoid loading large files into memory
        response = requests.get(image_url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Get content type from response or guess from filename
        content_type = response.headers.get('content-type', 'application/octet-stream')
        
        # Create streaming response
        response = HttpResponse(
            response.iter_content(chunk_size=8192),
            content_type=content_type
        )
        
        # Set content disposition for download
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Set cache control headers
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
        
    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {'error': f'Could not fetch the image: {str(e)}'}, 
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'error': 'An unexpected error occurred while processing your request'}, 
            status=500
        )


# API endpoints for AJAX requests
def api_photos(request):
    photos = Photo.objects.filter(is_active=True).order_by('-created_at')
    
    # Filter by location if provided
    location_filter = request.GET.get('location')
    if location_filter and location_filter != 'all':
        photos = photos.filter(location=location_filter)
    
    photos_data = []
    for photo in photos:
        try:
            if photo.has_image():
                image_url = None
                if photo.image and hasattr(photo.image, 'url'):
                    image_url = photo.image.url
                elif photo.image_url:
                    image_url = photo.image_url
                
                if image_url:  # Only include if we have a valid URL
                    photos_data.append({
                        'id': photo.id,
                        'title': str(photo.title) if photo.title else f'Photo {photo.id}',
                        'description': str(photo.description) if photo.description else '',
                        'location': photo.location,
                        'image_url': image_url,
                        'created_at': photo.created_at.isoformat() if hasattr(photo, 'created_at') else None
                    })
        except Exception as e:
            # Log the error but don't fail the entire request
            print(f"Error processing photo {photo.id}: {str(e)}")
            continue
            
    return JsonResponse({'photos': photos_data})


def api_videos(request):
    videos = Video.objects.filter(is_active=True).order_by('-created_at')
    
    # Filter by location if provided
    location_filter = request.GET.get('location')
    if location_filter and location_filter != 'all':
        videos = videos.filter(location=location_filter)
    
    videos_data = []
    for video in videos:
        video_url = None
        if video.video_file:
            video_url = video.video_file.url
        elif video.video_url:
            video_url = video.video_url
            
        if video_url:  # Only include videos with valid URLs
            videos_data.append({
                'id': video.id,
                'title': video.title or f'Video {video.id}',
                'description': video.description or '',
                'location': video.location,
                'video_url': video_url,
                'thumbnail_url': video.thumbnail.url if video.thumbnail else None,
                'created_at': video.created_at.isoformat() if hasattr(video, 'created_at') else None
            })
    return JsonResponse({'videos': videos_data})
