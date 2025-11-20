from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from .models import Course, Level, Session, UserProgress

class SessionInline(TranslationTabularInline):
    model = Session
    extra = 1
    fields = ['title', 'description', 'video_url', 'video_file', 'duration', 'order', 'is_active']

class LevelInline(TranslationTabularInline):
    model = Level
    extra = 1
    fields = ['name', 'description', 'order']

@admin.register(Course)
class CourseAdmin(TranslationAdmin):
    list_display = ['title', 'level', 'get_total_sessions', 'get_total_duration', 'price', 'rating', 'is_active', 'created_at']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['title']
    inlines = [LevelInline]
    
    def get_total_sessions(self, obj):
        return obj.get_total_sessions()
    get_total_sessions.short_description = 'Total Sessions'
    
    def get_total_duration(self, obj):
        return obj.get_total_duration()
    get_total_duration.short_description = 'Duration'

@admin.register(Level)
class LevelAdmin(TranslationAdmin):
    list_display = ['name', 'course', 'get_session_count', 'order']
    list_filter = ['course', 'order']
    search_fields = ['name', 'course__title']
    ordering = ['course', 'order']
    inlines = [SessionInline]
    
    def get_session_count(self, obj):
        return obj.sessions.count()
    get_session_count.short_description = 'Sessions'

@admin.register(Session)
class SessionAdmin(TranslationAdmin):
    list_display = ['title', 'level', 'course', 'duration', 'order', 'is_active', 'get_video_source']
    list_filter = ['level__course', 'level', 'is_active']
    search_fields = ['title', 'level__name', 'level__course__title']
    ordering = ['level__course', 'level__order', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'level', 'order', 'duration', 'is_active')
        }),
        ('Video Content', {
            'fields': ('video_url', 'video_file'),
            'description': 'Add YouTube URL or upload video file. Uploaded files take precedence over URLs.'
        }),
    )
    
    def course(self, obj):
        return obj.level.course.title
    course.short_description = 'Course'
    
    def get_video_source(self, obj):
        source = obj.get_video_source()
        if source == 'file':
            return format_html('<span style="color: green;">📁 Uploaded File</span>')
        elif source == 'url':
            if obj.is_youtube_url():
                return format_html('<span style="color: blue;">🔗 YouTube</span>')
            else:
                return format_html('<span style="color: orange;">🔗 External URL</span>')
        return format_html('<span style="color: red;">❌ No Video</span>')
    get_video_source.short_description = 'Video Source'

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'session', 'course', 'completed', 'progress_percentage', 'completed_at']
    list_filter = ['completed', 'session__level__course', 'completed_at']
    search_fields = ['user__username', 'session__title']
    ordering = ['user', 'session__level__course', 'session__level__order', 'session__order']
    readonly_fields = ['completed_at', 'last_watched_at']
    
    def course(self, obj):
        return obj.session.level.course.title
    course.short_description = 'Course'
