from django.db import models
from enum import Enum

class Location(Enum):
    LATINE_DHERMI = "Latine Dhermi"
    LATINE_DRYMADHES = "Latine Drymadhes"
    LATINE_DURRES = "Latine Durres"
    LATINE_TIKI = "Latine Tiki"

class MediaType(Enum):
    PHOTO = "Photo"
    VIDEO = "Video"

class Photo(models.Model):
    """Model for photo gallery"""
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True)
    location = models.CharField(
        max_length=50,
        choices=[(location.name, location.value) for location in Location],
        default=Location.LATINE_DHERMI.name
    )
    media_type = models.CharField(
        max_length=50,
        choices=[(media_type.name, media_type.value) for media_type in MediaType],
        default=MediaType.PHOTO.name
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='gallery/photos/', blank=True, null=True, help_text="Upload image file (JPG, PNG, GIF)")
    image_url = models.URLField(blank=True, null=True, help_text="Or provide image URL (e.g., from Instagram, Google Drive, etc.)")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        try:
            if self.title:
                return self.title
            if self.image and hasattr(self.image, 'url'):
                return self.image.url
            if self.image_url:
                return self.image_url
            return f"Photo {self.id}"
        except Exception:
            return f"Photo {self.id}"

    def get_image_source(self):
        """Return the type of image source"""
        if self.image:
            return f"File: {self.image.name}"
        elif self.image_url:
            return f"URL: {self.image_url}"
        return "No image"

    def get_media_url(self):
        """Get the URL for displaying the image"""
        try:
            if self.image:
                print(f"DEBUG: Getting URL for image {self.image.name}")
                print(f"DEBUG: Storage: {self.image.storage}")
                print(f"DEBUG: File exists: {self.image.storage.exists(self.image.name) if hasattr(self.image, 'storage') and hasattr(self.image.storage, 'exists') else 'N/A'}")
                return self.image.url
            elif self.image_url:
                print(f"DEBUG: Using image URL: {self.image_url}")
                return self.image_url
            print("DEBUG: No image or image_url available")
            return None
        except Exception as e:
            print(f"ERROR in get_media_url for photo {self.id}: {str(e)}")
            return None

    def has_image(self):
        """Check if photo has any image source"""
        return bool(self.image or self.image_url)

    def get_image_url(self):
        if self.image:
            return self.image.url
        elif self.image_url:
            return self.image_url
        else:
            return None

    def has_image(self):
        """Check if photo has any image source"""
        return bool(self.image or self.image_url)


class Video(models.Model):
    """Model for video gallery"""
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(
        max_length=50,
        choices=[(location.name, location.value) for location in Location],
        default=Location.LATINE_DHERMI.name
    )
    media_type = models.CharField(
        max_length=50,
        choices=[(media_type.name, media_type.value) for media_type in MediaType],
        default=MediaType.VIDEO.name
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    video_file = models.FileField(upload_to='gallery/videos/', blank=True, null=True, help_text='Upload video file (mp4, mov, etc.)')
    video_url = models.URLField(blank=True, null=True, help_text='Or provide a video URL')
    thumbnail = models.ImageField(upload_to='gallery/videos/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.video_url or (self.video_file.url if self.video_file else None) or "(no title)"

    def get_media_url(self):
        if self.video_file:
            return self.video_file.url
        elif self.video_url:
            return self.video_url
        return None
