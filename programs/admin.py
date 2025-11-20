from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import DanceStyle, Category, SkillLevel, Video, UserVideoAccess


class VideoInline(admin.TabularInline):
    model = Video
    extra = 0
    fields = ['title', 'is_free', 'price', 'duration', 'instructor_name', 'order', 'is_active']
    readonly_fields = ['slug']
    ordering = ['order']


class SkillLevelInline(admin.TabularInline):
    model = SkillLevel
    extra = 0
    fields = ['level', 'description', 'order', 'is_active']
    ordering = ['order']


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0
    fields = ['name', 'description', 'order', 'is_active']
    readonly_fields = ['slug']
    ordering = ['order']


@admin.register(DanceStyle)
class DanceStyleAdmin(admin.ModelAdmin):
    list_display = ['name', 'image_preview', 'categories_count', 'order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CategoryInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'order', 'is_active')
        }),
        ('Image', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="45" style="border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image"

    def categories_count(self, obj):
        count = obj.categories.filter(is_active=True).count()
        url = reverse('admin:programs_category_changelist') + f'?dance_style__id__exact={obj.id}'
        return format_html('<a href="{}">{} categories</a>', url, count)
    categories_count.short_description = "Categories"

    actions = ['activate_selected', 'deactivate_selected']

    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} dance styles activated.')
    activate_selected.short_description = "Activate selected dance styles"

    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} dance styles deactivated.')
    deactivate_selected.short_description = "Deactivate selected dance styles"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'dance_style', 'image_preview', 'skill_levels_count', 'order', 'is_active']
    list_filter = ['dance_style', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'dance_style__name']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [SkillLevelInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('dance_style', 'name', 'slug', 'description', 'order', 'is_active')
        }),
        ('Image', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="60" height="40" style="border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Image"

    def skill_levels_count(self, obj):
        count = obj.skill_levels.filter(is_active=True).count()
        url = reverse('admin:programs_skilllevel_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} levels</a>', url, count)
    skill_levels_count.short_description = "Skill Levels"

    actions = ['activate_selected', 'deactivate_selected']

    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} categories activated.')
    activate_selected.short_description = "Activate selected categories"

    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} categories deactivated.')
    deactivate_selected.short_description = "Deactivate selected categories"


@admin.register(SkillLevel)
class SkillLevelAdmin(admin.ModelAdmin):
    list_display = ['get_display_name', 'category', 'videos_count', 'free_videos_count', 'order', 'is_active']
    list_filter = ['category__dance_style', 'category', 'level', 'is_active', 'created_at']
    search_fields = ['description', 'category__name', 'category__dance_style__name']
    list_editable = ['order', 'is_active']
    inlines = [VideoInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'level', 'description', 'order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_display_name(self, obj):
        return f"{obj.category.name} - {obj.get_level_display()}"
    get_display_name.short_description = "Skill Level"

    def videos_count(self, obj):
        count = obj.videos.filter(is_active=True).count()
        url = reverse('admin:programs_video_changelist') + f'?skill_level__id__exact={obj.id}'
        return format_html('<a href="{}">{} videos</a>', url, count)
    videos_count.short_description = "Videos"

    def free_videos_count(self, obj):
        count = obj.videos.filter(is_active=True, is_free=True).count()
        return format_html('<span style="color: green;">{}</span>', count)
    free_videos_count.short_description = "Free Videos"

    actions = ['activate_selected', 'deactivate_selected']

    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} skill levels activated.')
    activate_selected.short_description = "Activate selected skill levels"

    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} skill levels deactivated.')
    deactivate_selected.short_description = "Deactivate selected skill levels"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'skill_level', 'thumbnail_preview', 'duration_display', 
        'instructor_name', 'price_display', 'view_count', 'order', 'is_active'
    ]
    list_filter = [
        'skill_level__category__dance_style', 'skill_level__category', 
        'skill_level__level', 'is_free', 'is_active', 'created_at'
    ]
    search_fields = ['title', 'description', 'instructor_name', 'skill_level__category__name']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'view_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('skill_level', 'title', 'slug', 'description', 'order', 'is_active')
        }),
        ('Video Content', {
            'fields': ('video_file', 'video_url', 'thumbnail', 'duration', 'instructor_name')
        }),
        ('Pricing & Access', {
            'fields': ('is_free', 'price')
        }),
        ('Statistics', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="60" height="40" style="border-radius: 4px;" />',
                obj.thumbnail.url
            )
        return "No Thumbnail"
    thumbnail_preview.short_description = "Thumbnail"

    def duration_display(self, obj):
        return obj.get_duration_display()
    duration_display.short_description = "Duration"

    def price_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: green; font-weight: bold;">FREE</span>')
        else:
            return format_html('<span style="color: #8B5CF6;">${}</span>', obj.price)
    price_display.short_description = "Price"

    actions = ['activate_selected', 'deactivate_selected', 'make_free', 'make_paid']

    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} videos activated.')
    activate_selected.short_description = "Activate selected videos"

    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} videos deactivated.')
    deactivate_selected.short_description = "Deactivate selected videos"

    def make_free(self, request, queryset):
        updated = queryset.update(is_free=True, price=0.00)
        self.message_user(request, f'{updated} videos made free.')
    make_free.short_description = "Make selected videos free"

    def make_paid(self, request, queryset):
        updated = queryset.update(is_free=False)
        self.message_user(request, f'{updated} videos made paid.')
    make_paid.short_description = "Make selected videos paid"


@admin.register(UserVideoAccess)
class UserVideoAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'purchased_at', 'expires_at', 'is_valid']
    list_filter = ['purchased_at', 'expires_at', 'video__skill_level__category__dance_style']
    search_fields = ['user__username', 'user__email', 'video__title']
    readonly_fields = ['purchased_at']
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'video', 'purchased_at', 'expires_at', 'payment_id')
        }),
    )

    def is_valid(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            return format_html('<span style="color: red;">✗ Expired</span>')
    is_valid.short_description = "Status"