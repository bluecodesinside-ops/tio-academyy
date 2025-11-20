from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class DanceStyle(models.Model):
    """Level 1: Dance Styles (e.g., Latina, Hip Hop, Contemporary, Ballroom)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    image = models.ImageField(upload_to='programs/dance_styles/', help_text="Recommended size: 400x300px")
    description = models.TextField(blank=True, help_text="Brief description of the dance style")
    order = models.PositiveIntegerField(default=0, help_text="Display order (0 = first)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Dance Style"
        verbose_name_plural = "Dance Styles"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('programs:dance_style', kwargs={'style_slug': self.slug})

    def get_categories_count(self):
        return self.categories.filter(is_active=True).count()


class Category(models.Model):
    """Level 2: Categories within a dance style (e.g., Salsa, Bachata, Merengue)"""
    dance_style = models.ForeignKey(DanceStyle, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    image = models.ImageField(upload_to='programs/categories/', help_text="Recommended size: 300x200px")
    description = models.TextField(blank=True, help_text="Brief description of the category")
    order = models.PositiveIntegerField(default=0, help_text="Display order within dance style")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ['dance_style', 'slug']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.dance_style.name} - {self.name}"

    def get_absolute_url(self):
        return reverse('programs:category', kwargs={
            'style_slug': self.dance_style.slug,
            'category_slug': self.slug
        })

    def get_skill_levels_count(self):
        return self.skill_levels.filter(is_active=True).count()


class SkillLevel(models.Model):
    """Level 3: Skill levels within a category (Basic, Intermediate, Advanced)"""
    LEVEL_CHOICES = [
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='skill_levels')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True, help_text="Description of what students will learn at this level")
    order = models.PositiveIntegerField(default=0, help_text="Display order within category")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'level']
        unique_together = ['category', 'level']
        verbose_name = "Skill Level"
        verbose_name_plural = "Skill Levels"

    def __str__(self):
        return f"{self.category.name} - {self.get_level_display()}"

    def get_absolute_url(self):
        return reverse('programs:skill_level', kwargs={
            'style_slug': self.category.dance_style.slug,
            'category_slug': self.category.slug,
            'level': self.level
        })

    def get_videos_count(self):
        return self.videos.filter(is_active=True).count()

    def get_free_videos_count(self):
        return self.videos.filter(is_active=True, is_free=True).count()

    def get_paid_videos_count(self):
        return self.videos.filter(is_active=True, is_free=False).count()


class Video(models.Model):
    """Level 4: Individual videos within a skill level"""
    skill_level = models.ForeignKey(SkillLevel, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Video content - either file upload or URL
    video_file = models.FileField(
        upload_to='programs/videos/', 
        blank=True, 
        null=True,
        help_text="Upload video file (MP4, MOV, AVI)"
    )
    video_url = models.URLField(
        blank=True, 
        null=True,
        help_text="YouTube or external video URL (alternative to file upload)"
    )
    
    # Video metadata
    thumbnail = models.ImageField(
        upload_to='programs/thumbnails/', 
        blank=True, 
        null=True,
        help_text="Video thumbnail (auto-generated if not provided)"
    )
    duration = models.PositiveIntegerField(
        default=0, 
        help_text="Duration in seconds"
    )
    instructor_name = models.CharField(max_length=100, default="Tio Academy")
    
    # Pricing and access
    is_free = models.BooleanField(
        default=False, 
        help_text="First video in each skill level should be free"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=9.99,
        validators=[MinValueValidator(0)],
        help_text="Price in USD (ignored if video is free)"
    )
    
    # Display and tracking
    order = models.PositiveIntegerField(default=0, help_text="Display order within skill level")
    is_active = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'title']
        unique_together = ['skill_level', 'slug']
        verbose_name = "Video"
        verbose_name_plural = "Videos"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Ensure first video in skill level is free
        if self.order == 0 and not self.is_free:
            self.is_free = True
            self.price = 0.00
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.skill_level} - {self.title}"

    def get_absolute_url(self):
        return reverse('programs:video_detail', kwargs={
            'style_slug': self.skill_level.category.dance_style.slug,
            'category_slug': self.skill_level.category.slug,
            'level': self.skill_level.level,
            'video_slug': self.slug
        })

    def get_video_source(self):
        """Get the primary video source (uploaded file takes precedence)"""
        if self.video_file:
            return 'file'
        elif self.video_url:
            return 'url'
        return None

    def is_youtube_url(self):
        """Check if the video URL is from YouTube"""
        if self.video_url:
            return 'youtube.com' in self.video_url or 'youtu.be' in self.video_url
        return False

    def get_youtube_embed_url(self):
        """Convert YouTube URL to embed format"""
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

    def get_duration_display(self):
        """Format duration as MM:SS or HH:MM:SS"""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def increment_view_count(self):
        """Increment view count by 1"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class UserVideoAccess(models.Model):
    """Track user access to paid videos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_access')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='user_access')
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True, help_text="Optional expiration date")
    payment_id = models.CharField(max_length=200, blank=True, help_text="Payment gateway transaction ID")
    
    class Meta:
        unique_together = ['user', 'video']
        verbose_name = "User Video Access"
        verbose_name_plural = "User Video Access"

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"

    def is_expired(self):
        """Check if access has expired"""
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False

    def is_valid(self):
        """Check if access is valid (not expired)"""
        return not self.is_expired()