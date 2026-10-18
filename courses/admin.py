from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline

from .models import Course, Level, Packet, Session, UserProgress


class SessionInline(TranslationTabularInline):
    """Flat video list for courses that are NOT sold as packets."""
    model = Session
    fk_name = 'course'
    extra = 1
    fields = ('order', 'title', 'cover', 'video_url', 'duration', 'is_free_preview', 'is_active')
    ordering = ['order', 'id']
    show_change_link = True
    verbose_name = 'Video'
    verbose_name_plural = 'Videos (tick Free preview on the one students can watch)'


class PacketVideoInline(TranslationTabularInline):
    model = Session
    fk_name = 'packet'
    extra = 1
    max_num = Packet.MAX_VIDEOS
    fields = ('order', 'title', 'cover', 'video_url', 'duration', 'is_free_preview', 'is_active')
    ordering = ['order', 'id']
    verbose_name = 'Video'
    verbose_name_plural = 'Videos in this packet'


@admin.register(Course)
class CourseAdmin(TranslationAdmin):
    list_display = ('cover_thumb', 'title', 'structure_badge', 'content_count', 'is_active', 'updated_at')
    list_display_links = ('cover_thumb', 'title')
    list_filter = ['sell_as_packets', 'level', 'is_active']
    list_editable = ['is_active']
    search_fields = ['title', 'description']
    ordering = ['title']
    readonly_fields = ['created_at', 'updated_at', 'cover_preview']
    change_list_template = 'admin/courses/course/change_list.html'
    change_form_template = 'admin/courses/course/change_form.html'
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Course', {
            'fields': ('title', 'slug', 'description', 'image', 'cover_preview', 'level', 'is_active'),
        }),
        ('How students buy', {
            'fields': ('sell_as_packets', 'price', 'duration'),
            'description': (
                'Packets on: this course is a container. Each packet has its own cover, price, and videos. '
                'Packets off: one price unlocks every video after the free preview.'
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj and obj.sell_as_packets:
            return []
        return [SessionInline]

    def cover_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:56px;height:40px;object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )
        return format_html('<span style="color:#999;">No cover</span>')
    cover_thumb.short_description = 'Cover'

    def cover_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:280px;border-radius:10px;" />', obj.image.url)
        return 'Upload a cover above'
    cover_preview.short_description = 'Cover preview'

    def structure_badge(self, obj):
        if obj.sell_as_packets:
            return format_html('<span style="color:#0f5132;font-weight:700;">Packets</span>')
        return format_html('<span style="color:#6c757d;">Whole course</span>')
    structure_badge.short_description = 'Structure'

    def content_count(self, obj):
        if obj.sell_as_packets:
            return f'{obj.packets.filter(is_active=True).count()} packets'
        return f'{obj.sessions.filter(is_active=True).count()} videos'
    content_count.short_description = 'Content'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        course = self.get_object(request, object_id)
        extra_context['course_packets'] = []
        extra_context['add_packet_url'] = ''
        if course and course.sell_as_packets:
            extra_context['course_packets'] = list(
                course.packets.all().prefetch_related('videos').order_by('order', 'id')
            )
            extra_context['add_packet_url'] = reverse('admin:courses_packet_add') + f'?course={course.pk}'
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def delete_model(self, request, obj):
        obj.delete()

    def delete_queryset(self, request, queryset):
        queryset.delete()


@admin.register(Packet)
class PacketAdmin(TranslationAdmin):
    list_display = ('cover_thumb', 'title', 'course', 'price', 'video_count_display', 'order', 'is_active')
    list_display_links = ('cover_thumb', 'title')
    list_filter = ['course', 'is_active']
    list_editable = ['price', 'order', 'is_active']
    search_fields = ['title', 'course__title']
    autocomplete_fields = ['course']
    inlines = [PacketVideoInline]
    readonly_fields = ['cover_preview', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    change_form_template = 'admin/courses/packet/change_form.html'
    fieldsets = (
        ('Packet', {
            'fields': ('course', 'title', 'slug', 'description', 'cover', 'cover_preview', 'price', 'order', 'is_active'),
            'description': 'This packet is a mini-course: cover + price + its videos.',
        }),
        ('Access window', {
            'fields': ('access_duration_days',),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        course_id = request.GET.get('course')
        if course_id:
            initial['course'] = course_id
            course = Course.objects.filter(pk=course_id).first()
            if course:
                initial['order'] = (course.packets.count() or 0) + 1
        return initial

    def cover_thumb(self, obj):
        url = obj.get_cover_url()
        if not url:
            return format_html('<span style="color:#999;">No cover</span>')
        return format_html(
            '<img src="{}" style="width:64px;height:44px;object-fit:cover;border-radius:6px;" />',
            url,
        )
    cover_thumb.short_description = 'Cover'

    def cover_preview(self, obj):
        url = obj.get_cover_url() if obj and obj.pk else None
        if not url:
            return 'Upload a cover above'
        return format_html('<img src="{}" style="max-width:280px;border-radius:10px;" />', url)
    cover_preview.short_description = 'Cover preview'

    def video_count_display(self, obj):
        return str(obj.video_count())
    video_count_display.short_description = 'Videos'

    def response_add(self, request, obj, post_url_continue=None):
        if obj.course_id:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse('admin:courses_course_change', args=[obj.course_id]))
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        if '_addanother' not in request.POST and '_continue' not in request.POST and obj.course_id:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse('admin:courses_course_change', args=[obj.course_id]))
        return super().response_change(request, obj)


@admin.register(Session)
class SessionAdmin(TranslationAdmin):
    list_display = ['title', 'course', 'packet', 'order', 'is_free_preview', 'is_active']
    list_filter = ['course', 'packet', 'is_active']
    search_fields = ['title', 'course__title']
    autocomplete_fields = ['course', 'packet']
    fieldsets = (
        ('Video', {
            'fields': ('course', 'packet', 'title', 'description', 'cover', 'order', 'duration', 'is_free_preview', 'is_active'),
        }),
        ('Playback URL', {
            'fields': ('video_url', 'video_file'),
        }),
        ('Legacy level (optional)', {
            'fields': ('level',),
            'classes': ('collapse',),
        }),
    )

    def get_model_perms(self, request):
        return {}


@admin.register(Level)
class LevelAdmin(TranslationAdmin):
    list_display = ['name', 'course', 'order']

    def get_model_perms(self, request):
        return {}


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'session', 'completed', 'progress_percentage']

    def get_model_perms(self, request):
        return {}
