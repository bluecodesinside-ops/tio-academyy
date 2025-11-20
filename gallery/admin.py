from django.contrib import admin
from django import forms
from django.forms.widgets import Widget
from .models import Photo, Video, Location, MediaType

class MultipleFileInput(Widget):
    template_name = 'django/forms/widgets/file.html'
    
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        super().__init__(attrs)
    
    def format_value(self, value):
        return None
    
    def value_from_datadict(self, data, files, name):
        return files.getlist(name)

class BulkUploadForm(forms.Form):
    MEDIA_CHOICES = [
        ('photo', 'Photos'),
        ('video', 'Videos'),
    ]
    
    media_type = forms.ChoiceField(choices=MEDIA_CHOICES, required=True, label="Upload Type")
    location = forms.ChoiceField(choices=[(loc.name, loc.value) for loc in Location], required=True)
    files = forms.FileField(
        widget=MultipleFileInput(attrs={'accept': 'image/*,video/*'}),
        required=True,
        label="Select Files"
    )

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['location', 'media_type', 'get_image_source', 'is_active', 'created_at']
    list_filter = ['location', 'media_type', 'is_active', 'created_at']
    ordering = ['-created_at']
    fields = ('location', 'media_type', 'image', 'image_url', 'is_active')
    search_fields = []
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='gallery_photo_bulk_upload'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['bulk_upload_url'] = 'bulk-upload/'
        return super().changelist_view(request, extra_context)
    
    def bulk_upload_view(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        
        if request.method == 'POST':
            location = request.POST.get('location')
            files = request.FILES.getlist('files')
            
            created_count = 0
            for file in files:
                if file and file.size > 0:  # Ensure file exists and has content
                    Photo.objects.create(
                        location=location,
                        media_type='PHOTO',
                        image=file,
                        is_active=True
                    )
                    created_count += 1
            
            messages.success(request, f'Successfully uploaded {created_count} photos.')
            return redirect('..')
        else:
            form = BulkUploadForm()
        
        return render(request, 'admin/gallery/photo_bulk_upload.html', {
            'form': form,
            'opts': self.model._meta,
            'title': 'Bulk Upload Photos'
        })

    def get_image_source(self, obj):
        return obj.get_image_source()
    get_image_source.short_description = 'Image Source'

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['location', 'media_type', 'is_active', 'created_at']
    list_filter = ['location', 'media_type', 'is_active', 'created_at']
    ordering = ['-created_at']
    fields = ('location', 'media_type', 'video_file', 'video_url', 'thumbnail', 'is_active')
    search_fields = []
    
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='video_bulk_upload'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        
        if request.method == 'POST':
            location = request.POST.get('location')
            files = request.FILES.getlist('files')
            
            created_count = 0
            for file in files:
                if file and file.size > 0:  # Ensure file exists and has content
                    Video.objects.create(
                        location=location,
                        media_type='VIDEO',
                        video_file=file,
                        is_active=True
                    )
                    created_count += 1
            
            messages.success(request, f'Successfully uploaded {created_count} videos.')
            return redirect('..')
        else:
            form = BulkUploadForm()
        
        return render(request, 'admin/gallery/video_bulk_upload.html', {
            'form': form,
            'opts': self.model._meta,
            'title': 'Bulk Upload Videos'
        })
