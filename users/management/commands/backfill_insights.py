"""Fill device and page insights from nginx access logs."""
from __future__ import annotations

import gzip
import re
from collections import defaultdict
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.management.base import BaseCommand

from users.geo import country_from_ip, ensure_database
from users.models import SiteInsightCount
from users.stats import SITE_TZ, _BOT_HINTS, device_from_ua, page_label

LOG_RE = re.compile(
    r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+)(?: HTTP/[^"]*)?" (\d+) \d+ "([^"]*)" "([^"]*)"'
)
SKIP = ('/static', '/media', '/admin', '/favicon', '/wp-', '/robots', '/.env')


def _open(path: Path):
    if path.name.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8', errors='replace')
    return path.open('r', encoding='utf-8', errors='replace')


def _day(stamp: str):
    raw, _, off = stamp.partition(' ')
    dt = datetime.strptime(raw, '%d/%b/%Y:%H:%M:%S')
    from datetime import timedelta, timezone as tz
    if off:
        sign = 1 if off.startswith('+') else -1
        dt = dt.replace(tzinfo=tz(sign * timedelta(hours=int(off[1:3]), minutes=int(off[3:5]))))
    else:
        dt = dt.replace(tzinfo=dt_timezone.utc)
    return dt.astimezone(SITE_TZ).date()


def iter_log_files(folder: Path):
    names = ['access.log', 'access.log.1'] + [f'access.log.{i}.gz' for i in range(2, 20)]
    for name in names:
        path = folder / name
        if path.exists():
            yield path


class Command(BaseCommand):
    help = 'Backfill phone/computer/country/page insights from nginx logs'

    def add_arguments(self, parser):
        parser.add_argument('--log-dir', default='/var/log/nginx')
        parser.add_argument('--skip-geo', action='store_true')

    def handle(self, *args, **options):
        folder = Path(options['log_dir'])
        if not options['skip_geo']:
            ensure_database(download=True)
        tallies = defaultdict(int)
        lines = 0
        for path in iter_log_files(folder):
            with _open(path) as handle:
                for line in handle:
                    parsed = LOG_RE.match(line)
                    if not parsed:
                        continue
                    ip, stamp, method, uri, status, referer, ua = parsed.groups()
                    if method != 'GET' or status not in ('200', '301', '302', '304'):
                        continue
                    ua_l = (ua or '').lower()
                    if any(hint in ua_l for hint in _BOT_HINTS):
                        continue
                    if 'zgrab' in ua_l or ua_l.startswith('curl/'):
                        continue
                    parsed_uri = urlparse(unquote(uri))
                    path_only = parsed_uri.path or '/'
                    if any(path_only.startswith(prefix) for prefix in SKIP):
                        continue
                    try:
                        day = _day(stamp)
                    except ValueError:
                        continue
                    lines += 1
                    if path_only.startswith('/stats'):
                        tallies[(day, SiteInsightCount.KIND_DEVICE, device_from_ua(ua))] += 1
                        country = country_from_ip(ip)
                        if country:
                            tallies[(day, SiteInsightCount.KIND_COUNTRY, country)] += 1
                        page = parse_qs(parsed_uri.query).get('p', [''])[0]
                        if not page and referer not in ('-', ''):
                            page = urlparse(referer).path
                        if page and not page.startswith('/stats') and not any(
                            page.startswith(prefix) for prefix in SKIP
                        ):
                            tallies[(day, SiteInsightCount.KIND_PAGE, page_label(page))] += 1
        written = 0
        for (day, kind, label), count in tallies.items():
            SiteInsightCount.objects.update_or_create(
                day=day, kind=kind, label=label, defaults={'count': count},
            )
            written += 1
        self.stdout.write(f'read {lines} hits, wrote {written} insight rows')
