from django.contrib import admin
from django.utils.html import format_html
from .models import SlideshowItem

@admin.register(SlideshowItem)
class SlideshowItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'media_type', 'thumbnail_preview', 'order', 'is_active', 'created_at')
    list_filter = ('media_type', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    list_editable = ('order', 'is_active')
    ordering = ('order', 'created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'media_type', 'order', 'is_active')
        }),
        ('Image Content', {
            'fields': ('image',),
            'classes': ('collapse',),
            'description': 'Upload an image for this slideshow item'
        }),
        ('Video Content', {
            'fields': ('video_file', 'video_url', 'video_thumbnail'),
            'classes': ('collapse',),
            'description': 'Upload a video file or provide a YouTube URL'
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Show thumbnail preview in admin list"""
        if obj.get_thumbnail_url():
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                obj.get_thumbnail_url()
            )
        return "No thumbnail"
    thumbnail_preview.short_description = 'Thumbnail'
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('order', 'created_at')