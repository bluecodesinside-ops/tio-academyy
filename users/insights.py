"""Assemble marketing insights for a day or for all tracked days."""
from __future__ import annotations

import calendar
from datetime import date, datetime

from django.db.models import Sum
from django.utils import timezone

from users.models import SiteDailyStat, SiteInsightCount
from users.stats import SITE_TZ, summary_numbers


def _counts(kind, day=None, limit=12):
    qs = SiteInsightCount.objects.filter(kind=kind)
    if day is not None:
        qs = qs.filter(day=day)
    else:
        qs = qs.values('label').annotate(count=Sum('count')).order_by('-count', 'label')
        return [{'label': row['label'], 'count': int(row['count'] or 0)} for row in qs[:limit]]
    return [{'label': row.label, 'count': row.count} for row in qs.order_by('-count', 'label')[:limit]]


def paid_items(day=None, limit=20):
    from catalog.models import UserAccessEntitlement
    from payments.models import Payment

    qs = UserAccessEntitlement.objects.select_related('package', 'product', 'product__linked_course')
    pays = Payment.objects.filter(status='succeeded').select_related('course')
    if day is not None:
        qs = qs.filter(started_at__date=day)
        pays = pays.filter(created_at__date=day)
    else:
        qs = qs.order_by('-started_at')[:limit]
        pays = pays.order_by('-created_at')[:limit]
        items = []
        for row in qs:
            name = row.package.title if row.package_id else row.product.title
            items.append({
                'label': name,
                'when': row.started_at,
                'amount': row.amount_paid,
            })
        for row in pays:
            items.append({
                'label': row.course.title if row.course_id else 'Course',
                'when': row.created_at,
                'amount': row.amount,
            })
        items.sort(key=lambda item: item['when'] or timezone.now(), reverse=True)
        return items[:limit]

    items = []
    for row in qs.order_by('-started_at')[:limit]:
        name = row.package.title if row.package_id else row.product.title
        items.append({'label': name, 'when': row.started_at, 'amount': row.amount_paid})
    for row in pays.order_by('-created_at')[:limit]:
        items.append({
            'label': row.course.title if row.course_id else 'Course',
            'when': row.created_at,
            'amount': row.amount,
        })
    items.sort(key=lambda item: item['when'] or timezone.now(), reverse=True)
    return items[:limit]


def day_stats(day):
    return SiteDailyStat.objects.filter(day=day).first()


def insight_bundle(day=None):
    traffic = summary_numbers()
    stat = day_stats(day) if day else None
    daily = list(SiteDailyStat.objects.order_by('-day').values(
        'day', 'unique_visitors', 'page_views', 'buy_clicks', 'purchases',
    ))
    if day:
        daily = [row for row in daily if row['day'] == day]
        headline = {
            'unique_visitors': stat.unique_visitors if stat else 0,
            'page_views': stat.page_views if stat else 0,
            'buy_clicks': stat.buy_clicks if stat else 0,
            'purchases': stat.purchases if stat else 0,
        }
    else:
        headline = traffic['all']
    countries = _counts(SiteInsightCount.KIND_COUNTRY, day, limit=20)
    devices = _counts(SiteInsightCount.KIND_DEVICE, day)
    pages = _counts(SiteInsightCount.KIND_PAGE, day)
    buy_clicks = _counts(SiteInsightCount.KIND_BUY, day)
    return {
        'day': day,
        'traffic': traffic,
        'headline': headline,
        'daily': daily,
        'countries': countries,
        'devices': devices,
        'pages': pages,
        'buy_clicks': buy_clicks,
        'paid_tracked': _counts(SiteInsightCount.KIND_PAY, day),
        'paid_items': paid_items(day),
        'toplist_tabs': [
            ('countries', countries, 'No country data yet.'),
            ('devices', devices, 'No device data yet.'),
            ('pages', pages, 'No page data yet.'),
            ('buy', buy_clicks, 'No buy clicks yet.'),
        ],
    }


def month_calendar(year, month):
    today = datetime.now(SITE_TZ).date()
    marked = set(
        SiteDailyStat.objects.filter(day__year=year, day__month=month).values_list('day', flat=True)
    )
    weeks = []
    for week in calendar.Calendar(0).monthdatescalendar(year, month):
        weeks.append([
            {
                'date': day,
                'iso': day.isoformat(),
                'in_month': day.month == month,
                'has_data': day in marked,
                'is_today': day == today,
            }
            for day in week
        ])
    first = date(year, month, 1)
    if month == 1:
        prev_y, prev_m = year - 1, 12
    else:
        prev_y, prev_m = year, month - 1
    if month == 12:
        next_y, next_m = year + 1, 1
    else:
        next_y, next_m = year, month + 1
    return {
        'year': year,
        'month': month,
        'title': first.strftime('%B %Y'),
        'weeks': weeks,
        'prev': f'{prev_y:04d}-{prev_m:02d}',
        'next': f'{next_y:04d}-{next_m:02d}',
        'today': today,
    }
