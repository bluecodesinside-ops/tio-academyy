"""Safe website counters. Failures must never block a page or a payment."""
import hashlib
import logging
import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from django.db.models import F, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)

SITE_TZ = ZoneInfo('Europe/Tirane')

_SKIP_PREFIXES = (
    '/admin', '/static', '/media', '/i18n', '/favicon', '/api/',
    '/payments/webhook', '/api/webhook', '/api/stripe',
)
_BOT_HINTS = ('bot', 'crawl', 'spider', 'slurp', 'preview', 'facebookexternalhit')
_PAGE_NAMES = {
    '/': 'Home',
    '/about/': 'About',
    '/courses/': 'Courses',
    '/contact/': 'Contact',
    '/login/': 'Sign in',
    '/register/': 'Create profile',
    '/dashboard/': 'My profile',
    '/gallery/': 'Gallery',
    '/faq/': 'FAQ',
    '/privacy/': 'Privacy',
    '/terms/': 'Terms',
}


def _today():
    return datetime.now(SITE_TZ).date()


def _stat_row(day=None):
    from users.models import SiteDailyStat
    day = day or _today()
    row, _ = SiteDailyStat.objects.get_or_create(day=day)
    return row


def device_from_ua(ua):
    text = (ua or '').lower()
    if 'ipad' in text or 'tablet' in text:
        return 'tablet'
    if 'mobile' in text or 'iphone' in text or 'android' in text:
        return 'phone'
    return 'computer'


def _strip_lang(path):
    path = path or '/'
    for prefix in ('/sq/', '/en/'):
        if path.startswith(prefix):
            path = '/' + path[len(prefix):]
            break
    if path in ('/sq', '/en'):
        return '/'
    if len(path) > 1 and not path.endswith('/'):
        path += '/'
    return path or '/'


def page_label(path):
    path = _strip_lang((path or '/').split('?')[0])
    if path in _PAGE_NAMES:
        return _PAGE_NAMES[path]
    packet = re.match(r'^/course/(\d+)/packet/(\d+)/', path)
    if packet:
        try:
            from courses.models import Packet
            row = Packet.objects.filter(
                pk=int(packet.group(2)), course_id=int(packet.group(1)),
            ).select_related('course').first()
            if row:
                return f'Packet: {row.title}'[:160]
        except Exception:
            pass
        return f'Packet {packet.group(2)}'
    course = re.match(r'^/course/(\d+)/', path)
    if course:
        try:
            from courses.models import Course
            row = Course.objects.filter(pk=int(course.group(1))).only('title').first()
            if row and row.title:
                return f'Course: {row.title}'[:160]
        except Exception:
            pass
        return f'Course {course.group(1)}'
    return path[:160]


def _page_from_request(request):
    path = (request.GET.get('p') or '').strip()
    if not path:
        referer = request.META.get('HTTP_REFERER') or ''
        path = urlparse(referer).path or ''
    if not path or path.startswith('/stats'):
        return ''
    if any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
        return ''
    return path


def bump(field, amount=1):
    from users.models import SiteDailyStat
    try:
        row = _stat_row()
        SiteDailyStat.objects.filter(pk=row.pk).update(**{field: F(field) + amount})
    except Exception:
        logger.exception('Could not bump website stat %s', field)


def bump_insight(kind, label, amount=1, day=None):
    from users.models import SiteInsightCount
    label = (label or 'Unknown')[:160]
    try:
        day = day or _today()
        row, _ = SiteInsightCount.objects.get_or_create(
            day=day, kind=kind, label=label, defaults={'count': 0},
        )
        SiteInsightCount.objects.filter(pk=row.pk).update(count=F('count') + amount)
    except Exception:
        logger.exception('Could not bump insight %s %s', kind, label)


def record_visit(request):
    from users.models import SiteDailyStat, SiteInsightCount, SiteVisitorDay
    try:
        if request.method not in ('GET', 'HEAD'):
            return
        ua = (request.META.get('HTTP_USER_AGENT') or '').lower()
        if any(hint in ua for hint in _BOT_HINTS):
            return
        day = _today()
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR') or ''
        ip = (forwarded.split(',')[0].strip() or request.META.get('REMOTE_ADDR') or '')
        raw = f'{ip}:{ua[:80]}'
        visitor_key = hashlib.sha256(raw.encode('utf-8')).hexdigest()[:32]
        row = _stat_row(day)
        SiteDailyStat.objects.filter(pk=row.pk).update(page_views=F('page_views') + 1)
        _, created = SiteVisitorDay.objects.get_or_create(day=day, visitor_key=visitor_key)
        if created:
            SiteDailyStat.objects.filter(pk=row.pk).update(unique_visitors=F('unique_visitors') + 1)
        device = device_from_ua(ua)
        bump_insight(SiteInsightCount.KIND_DEVICE, device, day=day)
        from users.geo import country_from_request
        country = country_from_request(request)
        if country:
            bump_insight(SiteInsightCount.KIND_COUNTRY, country, day=day)
        page = _page_from_request(request)
        if page:
            bump_insight(SiteInsightCount.KIND_PAGE, page_label(page), day=day)
    except Exception:
        logger.exception('Could not record website visit')


def record_buy_click(label='Buy', request=None):
    from users.models import SiteInsightCount
    bump('buy_clicks')
    name = (label or 'Buy')[:160]
    if request is not None:
        name = f'{name} ({device_from_ua(request.META.get("HTTP_USER_AGENT"))})'[:160]
    bump_insight(SiteInsightCount.KIND_BUY, name)


def record_purchase(label='Purchase', request=None):
    from users.models import SiteInsightCount
    bump('purchases')
    name = (label or 'Purchase')[:160]
    if request is not None:
        name = f'{name} ({device_from_ua(request.META.get("HTTP_USER_AGENT"))})'[:160]
    bump_insight(SiteInsightCount.KIND_PAY, name)


def summary_numbers():
    from catalog.models import UserAccessEntitlement
    from payments.models import Payment
    from users.models import SiteDailyStat, SiteVisitorDay

    today = _today()
    week_start = today - timedelta(days=6)
    qs = SiteDailyStat.objects.all()
    week = qs.filter(day__gte=week_start)

    def totals(rows):
        agg = rows.aggregate(
            page_views=Sum('page_views'),
            unique_visitors=Sum('unique_visitors'),
            buy_clicks=Sum('buy_clicks'),
            purchases=Sum('purchases'),
        )
        return {key: int(value or 0) for key, value in agg.items()}

    today_row = qs.filter(day=today).first()
    week_people = SiteVisitorDay.objects.filter(day__gte=week_start).values('visitor_key').distinct().count()
    all_people = SiteVisitorDay.objects.values('visitor_key').distinct().count()
    week_totals = totals(week)
    all_totals = totals(qs)
    week_totals['unique_visitors'] = week_people
    all_totals['unique_visitors'] = all_people
    return {
        'today': {
            'page_views': today_row.page_views if today_row else 0,
            'unique_visitors': today_row.unique_visitors if today_row else 0,
            'buy_clicks': today_row.buy_clicks if today_row else 0,
            'purchases': today_row.purchases if today_row else 0,
        },
        'week': week_totals,
        'all': all_totals,
        'purchases_ever': (
            UserAccessEntitlement.objects.count()
            + Payment.objects.filter(status='succeeded').count()
        ),
    }
