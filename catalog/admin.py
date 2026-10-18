from datetime import timedelta

from django.contrib import admin
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from catalog import admin_views
from catalog.forms import CourseProductForm, EntitlementGrantForm, MediaAssetForm, PackageForm, PricingTierForm
from catalog.models import CourseProduct, MediaAsset, Package, PricingTier, ProductKind, UserAccessEntitlement


class HiddenFromIndexMixin:
    def get_model_perms(self, request):
        return {}


class PricingTierInline(admin.TabularInline):
    model = PricingTier
    form = PricingTierForm
    extra = 0
    fields = (
        'name',
        'video_count',
        'price',
        'access_duration_days',
        'access_duration_months',
        'discount_percent',
        'is_active',
        'display_order',
    )
    verbose_name = 'Dance pricing tier'
    verbose_name_plural = 'Dance pricing tiers (1 / 3 / 6 videos)'


class PackageInline(admin.TabularInline):
    model = Package
    form = PackageForm
    extra = 0
    fields = (
        'chapter_number',
        'title',
        'individual_price',
        'cover',
        'is_active',
        'display_order',
    )
    show_change_link = True
    verbose_name = 'Physio chapter'
    verbose_name_plural = 'Physio chapters / packages'


class MediaAssetInline(admin.TabularInline):
    model = MediaAsset
    form = MediaAssetForm
    extra = 0
    fields = ('order', 'title', 'session', 'video_url', 'is_active')
    raw_id_fields = ['session']
    show_change_link = True


@admin.register(CourseProduct)
class CourseProductAdmin(HiddenFromIndexMixin, admin.ModelAdmin):
    form = CourseProductForm
    list_display = ('title', 'kind', 'is_active', 'tier_or_package_summary', 'bundle_badge', 'updated_at')
    list_filter = ('kind', 'is_active', 'bundle_enabled')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['linked_course']
    change_form_template = 'admin/catalog/courseproduct/change_form.html'

    fieldsets = (
        ('Product', {
            'fields': ('kind', 'title', 'slug', 'description', 'is_active', 'currency', 'linked_course'),
            'description': 'Dance products use pricing tiers. Physiotherapy products use 15 chapters plus an optional master bundle.',
        }),
        ('Physio master bundle', {
            'fields': (
                'bundle_enabled',
                'bundle_title',
                'bundle_price',
                'bundle_access_duration_days',
                'bundle_access_duration_months',
                'expected_package_count',
            ),
            'classes': ('catalog-bundle-fieldset', 'collapse'),
            'description': 'Optional. Student prices come from each package, not this bundle or the course price.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.kind == ProductKind.DANCE_VIDEOS:
            return [PricingTierInline]
        return [PackageInline]

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                '<int:product_id>/save-tiers/',
                self.admin_site.admin_view(admin_views.save_pricing_tiers),
                name='catalog_courseproduct_save_tiers',
            ),
            path(
                '<int:product_id>/save-physio-layout/',
                self.admin_site.admin_view(admin_views.save_physio_layout),
                name='catalog_courseproduct_save_physio_layout',
            ),
        ]
        return extra + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        product = self.get_object(request, object_id)
        if product:
            extra_context.update({
                'catalog_kind': product.kind,
                'catalog_is_dance': product.kind == ProductKind.DANCE_VIDEOS,
                'catalog_is_physio': product.kind == ProductKind.PHYSIO_PACKAGES,
                'catalog_tiers': list(product.pricing_tiers.order_by('display_order', 'video_count')),
                'catalog_package_count': product.packages.filter(is_active=True).count(),
                'catalog_physio_packages': list(product.packages.filter(is_active=True).order_by('display_order', 'chapter_number', 'id')),
                'catalog_physio_videos': [],
                'save_tiers_url': reverse('admin:catalog_courseproduct_save_tiers', args=[product.pk]),
                'save_physio_layout_url': reverse('admin:catalog_courseproduct_save_physio_layout', args=[product.pk]),
            })
            if product.kind == ProductKind.PHYSIO_PACKAGES and product.linked_course_id:
                assets_by_session = {
                    asset.session_id: asset
                    for asset in product.media_assets.filter(session_id__isnull=False)
                }
                extra_context['catalog_physio_videos'] = [
                    {
                        'session_id': session.id,
                        'title': session.title,
                        'package_id': getattr(assets_by_session.get(session.id), 'package_id', None),
                    }
                    for session in product.linked_course.get_ordered_sessions()
                ]
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def tier_or_package_summary(self, obj):
        if obj.kind == ProductKind.DANCE_VIDEOS:
            return f'{obj.pricing_tiers.filter(is_active=True).count()} tiers'
        return f'{obj.packages.filter(is_active=True).count()}/{obj.expected_package_count} chapters'
    tier_or_package_summary.short_description = 'Catalog'

    def bundle_badge(self, obj):
        if obj.kind != ProductKind.PHYSIO_PACKAGES:
            return '—'
        if obj.bundle_enabled:
            return format_html('<span style="color:#157347;font-weight:600;">€{} bundle on</span>', obj.bundle_price)
        return format_html('<span style="color:#6c757d;">bundle off</span>')
    bundle_badge.short_description = 'Bundle'


@admin.register(Package)
class PackageAdmin(HiddenFromIndexMixin, admin.ModelAdmin):
    form = PackageForm
    list_display = ('cover_preview', 'title', 'product', 'chapter_number', 'individual_price', 'video_count', 'is_active')
    list_display_links = ('cover_preview', 'title')
    list_filter = ('product', 'is_active')
    search_fields = ('title', 'description', 'product__title')
    list_editable = ('individual_price', 'is_active')
    inlines = [MediaAssetInline]
    autocomplete_fields = ['product']
    change_form_template = 'admin/catalog/package/change_form.html'
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('cover_preview',)

    fieldsets = (
        ('Package', {
            'fields': (
                'product',
                'chapter_number',
                'title',
                'slug',
                'description',
                'individual_price',
                'cover',
                'cover_preview',
                'access_duration_days',
                'is_active',
                'display_order',
            ),
            'description': 'Upload a cover for this packet. Students see it when they choose packages.',
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                '<int:package_id>/map-videos/',
                self.admin_site.admin_view(admin_views.map_chapter_videos),
                name='catalog_package_map_videos',
            ),
        ]
        return extra + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        package = self.get_object(request, object_id)
        if package:
            product = package.product
            extra_context['map_videos_url'] = reverse('admin:catalog_package_map_videos', args=[package.pk])
            extra_context['mapped_assets'] = list(package.media_assets.filter(is_active=True).order_by('order', 'id'))
            extra_context['available_sessions'] = []
            if product.linked_course_id:
                extra_context['available_sessions'] = list(
                    product.linked_course.sessions.filter(is_active=True).order_by('order', 'id')
                )
            extra_context['unassigned_assets'] = list(
                product.media_assets.filter(is_active=True).exclude(package=package).order_by('order', 'id')[:80]
            )
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def cover_preview(self, obj):
        url = obj.get_cover_url() if obj and obj.pk else None
        if not url:
            return '—'
        return format_html(
            '<img src="{}" alt="" style="height:48px;width:72px;object-fit:cover;border-radius:4px;" />',
            url,
        )
    cover_preview.short_description = 'Cover'

    def video_count(self, obj):
        return obj.media_assets.filter(is_active=True).count()
    video_count.short_description = 'Videos'


@admin.register(PricingTier)
class PricingTierAdmin(HiddenFromIndexMixin, admin.ModelAdmin):
    form = PricingTierForm
    list_display = ('name', 'product', 'video_count', 'price', 'access_duration_days', 'discount_percent', 'is_active')
    list_filter = ('product', 'is_active')
    list_editable = ('price', 'access_duration_days', 'discount_percent', 'is_active')
    search_fields = ('name', 'product__title')


@admin.register(MediaAsset)
class MediaAssetAdmin(HiddenFromIndexMixin, admin.ModelAdmin):
    form = MediaAssetForm
    list_display = ('title', 'product', 'package', 'session', 'is_active', 'order')
    list_filter = ('product', 'package', 'is_active')
    search_fields = ('title', 'description', 'video_url')
    list_editable = ('order', 'is_active')
    autocomplete_fields = ['product', 'package']
    raw_id_fields = ['session']
    filter_horizontal = ['allowed_tiers']


@admin.register(UserAccessEntitlement)
class UserAccessEntitlementAdmin(admin.ModelAdmin):
    form = EntitlementGrantForm
    list_display = ('student_email', 'purchased_item', 'started_at', 'expires_at', 'is_active', 'valid_badge', 'amount_paid')
    list_filter = ('scope', 'is_active', 'product', 'started_at')
    search_fields = ('user__username', 'user__email', 'product__title', 'package__title', 'stripe_session_id')
    autocomplete_fields = ['user', 'product', 'pricing_tier', 'package', 'granted_by']
    filter_horizontal = ['media_assets']
    readonly_fields = ('stripe_session_id', 'amount_paid', 'currency', 'created_at', 'updated_at')
    date_hierarchy = 'started_at'
    list_select_related = ('user', 'product', 'package')

    fieldsets = (
        ('Student & purchase', {
            'fields': ('user', 'product', 'scope', 'pricing_tier', 'package', 'media_assets', 'is_active', 'notes'),
        }),
        ('Access length', {
            'fields': ('access_length', 'started_at', 'expires_at'),
            'description': 'Use 1 month / 3 months / 6 months / lifetime. Blank expiry = lifetime.',
        }),
        ('Payment', {
            'fields': ('stripe_session_id', 'amount_paid', 'currency', 'granted_by'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ('set_one_month', 'set_three_months', 'set_six_months', 'set_lifetime')

    def save_model(self, request, obj, form, change):
        if not obj.started_at:
            obj.started_at = timezone.now()
        if not obj.granted_by_id and request.user.is_staff:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

    def _set_length(self, request, queryset, days, label):
        now = timezone.now()
        updated = 0
        for obj in queryset:
            obj.started_at = obj.started_at or now
            obj.expires_at = None if not days else now + timedelta(days=days)
            obj.is_active = True
            obj.save(update_fields=['started_at', 'expires_at', 'is_active'])
            updated += 1
        self.message_user(request, f'Set {updated} purchase(s) to {label}.')

    def set_one_month(self, request, queryset):
        self._set_length(request, queryset, 30, '1 month')
    set_one_month.short_description = 'Set access to 1 month'

    def set_three_months(self, request, queryset):
        self._set_length(request, queryset, 90, '3 months')
    set_three_months.short_description = 'Set access to 3 months'

    def set_six_months(self, request, queryset):
        self._set_length(request, queryset, 180, '6 months')
    set_six_months.short_description = 'Set access to 6 months'

    def set_lifetime(self, request, queryset):
        self._set_length(request, queryset, 0, 'lifetime')
    set_lifetime.short_description = 'Set access to lifetime'

    def student_email(self, obj):
        return obj.user.email or obj.user.username
    student_email.short_description = 'Student'
    student_email.admin_order_field = 'user__email'

    def purchased_item(self, obj):
        if obj.package_id:
            return obj.package.title
        if obj.scope == 'full_bundle':
            return f'{obj.product.title} (all packages)'
        return obj.product.title
    purchased_item.short_description = 'Bought'

    def valid_badge(self, obj):
        if obj.is_currently_valid():
            remaining = obj.remaining_days()
            label = f'{remaining}d left' if obj.expires_at else 'lifetime'
            return format_html('<span style="color:#157347;font-weight:600;">{}</span>', label)
        return format_html('<span style="color:#dc3545;font-weight:600;">expired</span>')
    valid_badge.short_description = 'Live?'


def _hide_catalog_app(request, app_label=None):
    """Hide catalog internals; keep Purchases visible under Users."""
    app_list = _ORIGINAL_GET_APP_LIST(request, app_label)
    catalog = next((app for app in app_list if app.get('app_label') == 'catalog'), None)
    filtered = [app for app in app_list if app.get('app_label') != 'catalog']
    purchases = []
    if catalog:
        purchases = [model for model in catalog.get('models', []) if model.get('object_name') == 'UserAccessEntitlement']
    users = next((app for app in filtered if app.get('app_label') == 'users'), None)
    if users and purchases:
        users['models'] = purchases + users.get('models', [])
    return filtered


_ORIGINAL_GET_APP_LIST = admin.site.get_app_list
admin.site.get_app_list = _hide_catalog_app
