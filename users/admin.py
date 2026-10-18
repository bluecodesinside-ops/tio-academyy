from datetime import date, datetime

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html_join

from catalog.models import UserAccessEntitlement
from users.exports import excel_response, pdf_response
from users.models import SiteDailyStat, UserProfile


class PurchaseInline(admin.TabularInline):
    model = UserAccessEntitlement
    fk_name = 'user'
    extra = 0
    fields = ('product', 'package', 'scope', 'started_at', 'expires_at', 'is_active', 'amount_paid')
    readonly_fields = ('amount_paid',)
    autocomplete_fields = ['product', 'package']
    show_change_link = True
    verbose_name = 'Purchase'
    verbose_name_plural = 'Purchases (1 / 3 / 6 months)'


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 0
    can_delete = False
    fields = ('subscription_status', 'has_lifetime_access', 'stripe_customer_id')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'last_login', 'subscription_status', 'has_lifetime_access', 'created_at')
    list_filter = ('subscription_status', 'has_lifetime_access')
    search_fields = ('user__username', 'user__email', 'stripe_customer_id', 'stripe_subscription_id')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user',)

    def user_email(self, obj):
        return obj.user.email or obj.user.username
    user_email.short_description = 'Student'
    user_email.admin_order_field = 'user__email'

    def last_login(self, obj):
        return obj.user.last_login
    last_login.short_description = 'Last login'
    last_login.admin_order_field = 'user__last_login'


class AcademyUserAdmin(BaseUserAdmin):
    list_display = ('email', 'last_login', 'date_joined', 'is_active', 'purchases_summary')
    list_filter = ('is_active', 'is_staff', 'last_login', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-last_login',)
    inlines = [UserProfileInline, PurchaseInline]

    def purchases_summary(self, obj):
        rows = list(
            obj.access_entitlements.select_related('package', 'product').order_by('-started_at')[:6]
        )
        if not rows:
            return '—'
        parts = []
        for entitlement in rows:
            name = entitlement.package.title if entitlement.package_id else entitlement.product.title
            if entitlement.is_currently_valid():
                until = entitlement.expires_at.strftime('%d %b %Y') if entitlement.expires_at else 'lifetime'
                parts.append(f'{name} (until {until})')
            else:
                parts.append(f'{name} (expired)')
        return format_html_join('<br>', '{}', ((part,) for part in parts))
    purchases_summary.short_description = 'Bought'


@admin.register(SiteDailyStat)
class SiteDailyStatAdmin(admin.ModelAdmin):
    change_list_template = 'admin/users/sitedailystat/change_list.html'
    list_display = ('day', 'unique_visitors', 'page_views', 'buy_clicks', 'purchases')
    ordering = ('-day',)
    readonly_fields = ('day', 'page_views', 'unique_visitors', 'buy_clicks', 'purchases')
    date_hierarchy = 'day'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        custom = [
            path(
                'export/excel/',
                self.admin_site.admin_view(self.export_excel_view),
                name='%s_%s_export_excel' % info,
            ),
            path(
                'export/pdf/',
                self.admin_site.admin_view(self.export_pdf_view),
                name='%s_%s_export_pdf' % info,
            ),
            path(
                'day/<str:day>/',
                self.admin_site.admin_view(self.day_view),
                name='%s_%s_day' % info,
            ),
        ]
        return custom + super().get_urls()

    def _day_from_request(self, request):
        raw = request.GET.get('day')
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    def export_excel_view(self, request):
        return excel_response(self._day_from_request(request))

    def export_pdf_view(self, request):
        return pdf_response(self._day_from_request(request))

    def day_view(self, request, day):
        try:
            picked = date.fromisoformat(day)
        except ValueError:
            raise Http404('Unknown date')
        from users.insights import insight_bundle
        report = insight_bundle(picked)
        return render(request, 'admin/users/sitedailystat/day.html', {
            **self.admin_site.each_context(request),
            'title': f'Insights {picked.isoformat()}',
            'opts': self.model._meta,
            'report': report,
            'picked': picked,
        })

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        from users.insights import insight_bundle, month_calendar
        from users.stats import SITE_TZ, summary_numbers
        today = datetime.now(SITE_TZ).date()
        cal = request.GET.get('cal') or today.strftime('%Y-%m')
        try:
            year, month = [int(part) for part in cal.split('-')]
            date(year, month, 1)
        except (ValueError, TypeError):
            year, month = today.year, today.month
        traffic = summary_numbers()
        extra_context['traffic'] = traffic
        extra_context['traffic_cards'] = [
            ('Today', traffic['today']),
            ('Last 7 days', traffic['week']),
            ('Since tracking', traffic['all']),
        ]
        extra_context['calendar'] = month_calendar(year, month)
        extra_context['overview'] = insight_bundle()
        extra_context['today_report'] = insight_bundle(today)
        return super().changelist_view(request, extra_context=extra_context)


admin.site.unregister(User)
admin.site.register(User, AcademyUserAdmin)
