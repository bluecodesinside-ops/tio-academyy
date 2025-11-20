from django.db import models
from django.utils.text import slugify

class SlideshowItem(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    title = models.CharField(max_length=200, help_text="Title for this slideshow item")
    description = models.TextField(blank=True, help_text="Optional description")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='image')
    
    # Image fields
    image = models.ImageField(
        upload_to='slideshow/images/', 
        blank=True, 
        null=True,
        help_text="Upload an image for this slideshow item"
    )
    
    # Video fields
    video_file = models.FileField(
        upload_to='slideshow/videos/', 
        blank=True, 
        null=True,
        help_text="Upload a video file (MP4, MOV, AVI)"
    )
    video_url = models.URLField(
        blank=True, 
        null=True,
        help_text="YouTube or external video URL"
    )
    video_thumbnail = models.ImageField(
        upload_to='slideshow/video_thumbnails/', 
        blank=True, 
        null=True,
        help_text="Custom thumbnail for video (optional)"
    )
    
    # Display settings
    order = models.IntegerField(default=0, help_text="Order in which items appear (lower numbers first)")
    is_active = models.BooleanField(default=True, help_text="Whether this item is visible in the slideshow")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Slideshow Item"
        verbose_name_plural = "Slideshow Items"
    
    def __str__(self):
        return f"{self.title} ({self.get_media_type_display()})"
    
    def get_media_url(self):
        """Get the URL for the media content"""
        if self.media_type == 'image' and self.image:
            return self.image.url
        elif self.media_type == 'video' and self.video_file:
            return self.video_file.url
        elif self.media_type == 'video' and self.video_url:
            return self.video_url
        return None
    
    def get_thumbnail_url(self):
        """Get the thumbnail URL for this item"""
        if self.media_type == 'image' and self.image:
            return self.image.url
        elif self.media_type == 'video' and self.video_thumbnail:
            return self.video_thumbnail.url
        elif self.media_type == 'video' and self.video_file:
            return self.video_file.url
        return None
    
    def is_youtube_url(self):
        """Check if video URL is a YouTube URL"""
        if self.video_url:
            return 'youtube.com' in self.video_url or 'youtu.be' in self.video_url
        return False
    
    def get_youtube_embed_url(self):
        """Convert YouTube URL to embed URL"""
        if not self.is_youtube_url():
            return None
        
        # Handle different YouTube URL formats
        if 'youtube.com/watch?v=' in self.video_url:
            video_id = self.video_url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in self.video_url:
            video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
        else:
            return None
        
        return f"https://www.youtube.com/embed/{video_id}"