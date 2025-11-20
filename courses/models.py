from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    """Model for dance courses"""
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='courses/', blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration = models.CharField(max_length=50, help_text="e.g., '12 sessions'")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    def get_total_sessions(self):
        """Get total number of sessions across all levels"""
        return sum(level.sessions.count() for level in self.levels.all())
    
    def get_total_duration(self):
        """Get total duration in minutes"""
        total_minutes = sum(session.duration for level in self.levels.all() for session in level.sessions.all())
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

class Level(models.Model):
    """Model for course levels (Beginner, Intermediate, Advanced)"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='levels')
    name = models.CharField(max_length=50)
    description = models.TextField()
    order = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.title} - {self.name}"

class Session(models.Model):
    """Model for individual sessions within a level"""
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField(blank=True, null=True, help_text="YouTube or external video URL")
    video_file = models.FileField(upload_to='videos/sessions/', blank=True, null=True, help_text="Upload video file (MP4, MOV, AVI)")
    duration = models.IntegerField(help_text="Duration in minutes", default=20)
    order = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['level', 'order']
    
    def __str__(self):
        return f"{self.level.course.title} - {self.level.name} - {self.title}"
    
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

class UserProgress(models.Model):
    """Model to track user progress through courses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    progress_percentage = models.IntegerField(default=0, help_text="Progress percentage (0-100)")
    last_watched_position = models.IntegerField(default=0, help_text="Last watched position in seconds")
    last_watched_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'session']
    
    def __str__(self):
        return f"{self.user.username} - {self.session.title}"
    
    def is_level_completed(self):
        """Check if the entire level is completed"""
        level_sessions = self.session.level.sessions.all()
        completed_sessions = UserProgress.objects.filter(
            user=self.user,
            session__in=level_sessions,
            completed=True
        ).count()
        return completed_sessions == level_sessions.count()
    
    def get_next_session(self):
        """Get the next session in the course"""
        current_session = self.session
        next_session = Session.objects.filter(
            level__course=current_session.level.course,
            level__order__gte=current_session.level.order,
            order__gt=current_session.order
        ).first()
        
        if not next_session:
            # Try next level
            next_session = Session.objects.filter(
                level__course=current_session.level.course,
                level__order=current_session.level.order + 1,
                order=1
            ).first()
        
        return next_session
