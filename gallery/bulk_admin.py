from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from .models import Photo, Video, Location, MediaType
from .admin import BulkUploadForm

class BulkUploadAdmin:
    """Unified bulk upload admin for photos and videos"""
    
    def get_urls(self):
        urls = [
            path('bulk-upload/', self.bulk_upload_view, name='gallery_bulk_upload'),
        ]
        return urls
    
    def bulk_upload_view(self, request):
        if request.method == 'POST':
            form = BulkUploadForm(request.POST, request.FILES)
            if form.is_valid():
                media_type = form.cleaned_data['media_type']
                location = form.cleaned_data['location']
                files = request.FILES.getlist('files')
                
                created_count = 0
                for file in files:
                    if media_type == 'photo':
                        Photo.objects.create(
                            location=location,
                            media_type='PHOTO',
                            image=file,
                            is_active=True
                        )
                    else:  # video
                        Video.objects.create(
                            location=location,
                            media_type='VIDEO',
                            video_file=file,
                            is_active=True
                        )
                    created_count += 1
                
                messages.success(request, f'Successfully uploaded {created_count} {media_type}(s)!')
                return redirect('admin:gallery_bulk_upload')
        else:
            form = BulkUploadForm()
        
        # Get all photos and videos for display
        photos = Photo.objects.filter(is_active=True).order_by('-created_at')[:50]
        videos = Video.objects.filter(is_active=True).order_by('-created_at')[:50]
        
        context = {
            'form': form,
            'photos': photos,
            'videos': videos,
            'title': 'Bulk Upload Media',
        }
        return render(request, 'admin/gallery/bulk_upload.html', context)

# Register the bulk upload admin
bulk_admin = BulkUploadAdmin()
