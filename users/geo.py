"""IP → country name for website insights. Failures must never block a visit."""
from __future__ import annotations

import bisect
import ipaddress
import logging
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

IPV4_URL = (
    'https://cdn.jsdelivr.net/npm/@ip-location-db/geo-whois-asn-country/'
    'geo-whois-asn-country-ipv4.csv'
)
IPV6_URL = (
    'https://cdn.jsdelivr.net/npm/@ip-location-db/geo-whois-asn-country/'
    'geo-whois-asn-country-ipv6.csv'
)

COUNTRY_NAMES = {
    'AD': 'Andorra', 'AE': 'United Arab Emirates', 'AF': 'Afghanistan',
    'AL': 'Albania', 'AM': 'Armenia', 'AR': 'Argentina', 'AT': 'Austria',
    'AU': 'Australia', 'AZ': 'Azerbaijan', 'BA': 'Bosnia and Herzegovina',
    'BD': 'Bangladesh', 'BE': 'Belgium', 'BG': 'Bulgaria', 'BH': 'Bahrain',
    'BR': 'Brazil', 'BY': 'Belarus', 'CA': 'Canada', 'CH': 'Switzerland',
    'CL': 'Chile', 'CN': 'China', 'CO': 'Colombia', 'CR': 'Costa Rica',
    'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DE': 'Germany', 'DK': 'Denmark',
    'DZ': 'Algeria', 'EE': 'Estonia', 'EG': 'Egypt', 'ES': 'Spain',
    'FI': 'Finland', 'FR': 'France', 'GB': 'United Kingdom', 'GE': 'Georgia',
    'GR': 'Greece', 'HK': 'Hong Kong', 'HR': 'Croatia', 'HU': 'Hungary',
    'ID': 'Indonesia', 'IE': 'Ireland', 'IL': 'Israel', 'IN': 'India',
    'IQ': 'Iraq', 'IR': 'Iran', 'IS': 'Iceland', 'IT': 'Italy',
    'JP': 'Japan', 'KE': 'Kenya', 'KR': 'South Korea', 'KW': 'Kuwait',
    'KZ': 'Kazakhstan', 'LB': 'Lebanon', 'LT': 'Lithuania', 'LU': 'Luxembourg',
    'LV': 'Latvia', 'MA': 'Morocco', 'MD': 'Moldova', 'ME': 'Montenegro',
    'MK': 'North Macedonia', 'MT': 'Malta', 'MX': 'Mexico', 'MY': 'Malaysia',
    'NG': 'Nigeria', 'NL': 'Netherlands', 'NO': 'Norway', 'NZ': 'New Zealand',
    'PK': 'Pakistan', 'PL': 'Poland', 'PT': 'Portugal', 'QA': 'Qatar',
    'RO': 'Romania', 'RS': 'Serbia', 'RU': 'Russia', 'SA': 'Saudi Arabia',
    'SE': 'Sweden', 'SG': 'Singapore', 'SI': 'Slovenia', 'SK': 'Slovakia',
    'TH': 'Thailand', 'TN': 'Tunisia', 'TR': 'Turkey', 'TW': 'Taiwan',
    'UA': 'Ukraine', 'US': 'United States', 'UZ': 'Uzbekistan',
    'VN': 'Vietnam', 'XK': 'Kosovo', 'ZA': 'South Africa',
}

_data_dir = Path(__file__).resolve().parent / 'data'
_v4 = None
_v6 = None


def set_data_dir(path):
    global _data_dir, _v4, _v6
    _data_dir = Path(path)
    _v4 = None
    _v6 = None


def country_name(code):
    code = (code or '').strip().upper()
    if len(code) != 2 or code in ('XX', 'T1', 'A1', 'A2'):
        return ''
    return COUNTRY_NAMES.get(code, code)


def _ip_int(text):
    return int(ipaddress.ip_address(text))


def _load_csv(path):
    starts, ends, codes = [], [], []
    with path.open('r', encoding='utf-8', errors='replace') as handle:
        for line in handle:
            parts = line.strip().split(',')
            if len(parts) < 3:
                continue
            try:
                start, end = _ip_int(parts[0]), _ip_int(parts[1])
            except ValueError:
                continue
            starts.append(start)
            ends.append(end)
            codes.append(parts[2].strip().upper())
    return starts, ends, codes


def _download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix('.tmp')
    req = urllib.request.Request(url, headers={'User-Agent': 'TioAcademyInsights/1'})
    with urllib.request.urlopen(req, timeout=90) as resp, tmp.open('wb') as out:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)
    tmp.replace(dest)


def ensure_database(download=True):
    global _v4, _v6
    _data_dir.mkdir(parents=True, exist_ok=True)
    v4_path = _data_dir / 'ip-country-ipv4.csv'
    v6_path = _data_dir / 'ip-country-ipv6.csv'
    try:
        if download and not v4_path.exists():
            logger.info('Downloading IPv4 country database')
            _download(IPV4_URL, v4_path)
        if download and not v6_path.exists():
            logger.info('Downloading IPv6 country database')
            _download(IPV6_URL, v6_path)
    except Exception:
        logger.exception('Could not download country database')
    if _v4 is not None:
        return bool(_v4[0] or (_v6 and _v6[0]))
    if not v4_path.exists() and not v6_path.exists():
        return False
    _v4 = _load_csv(v4_path) if v4_path.exists() else ([], [], [])
    _v6 = _load_csv(v6_path) if v6_path.exists() else ([], [], [])
    return bool(_v4[0] or _v6[0])


def _lookup(tables, value):
    starts, ends, codes = tables
    if not starts:
        return ''
    idx = bisect.bisect_right(starts, value) - 1
    if idx >= 0 and starts[idx] <= value <= ends[idx]:
        return codes[idx]
    return ''


def country_from_ip(ip):
    ip = (ip or '').strip()
    if not ip:
        return ''
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ''
    if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_multicast:
        return ''
    try:
        ensure_database(download=False)
        tables = _v6 if addr.version == 6 else _v4
        if not tables:
            return ''
        return country_name(_lookup(tables, int(addr)))
    except Exception:
        logger.exception('Could not resolve country for IP')
        return ''


def country_from_request(request):
    header = (request.META.get('HTTP_CF_IPCOUNTRY') or '').strip().upper()
    named = country_name(header)
    if named:
        return named
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR') or ''
    ip = (forwarded.split(',')[0].strip() or request.META.get('REMOTE_ADDR') or '')
    return country_from_ip(ip)
