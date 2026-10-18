from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django import template
import re

register = template.Library()

SALE_OFF_PERCENT = Decimal('70')


def compare_at_price(sale_price):
    """Listed price is the sale amount (70% off). Original = sale / 0.30."""
    try:
        amount = Decimal(str(sale_price))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if amount <= 0:
        return None
    keep = (Decimal('100') - SALE_OFF_PERCENT) / Decimal('100')
    original = (amount / keep).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    if original == original.to_integral_value():
        return original.quantize(Decimal('1'))
    return original


def _display_amount(amount):
    if amount is None:
        return None
    if amount == amount.to_integral_value():
        return amount.quantize(Decimal('1'))
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


@register.inclusion_tag('components/sale_price.html')
def sale_price(price, currency='€'):
    """Was/now price: €39 sale = ~~€130~~ €39 70% off."""
    try:
        now = Decimal(str(price))
    except (InvalidOperation, TypeError, ValueError):
        now = None
    if now is None or now <= 0:
        return {'was': None, 'now': None, 'currency': currency, 'off': SALE_OFF_PERCENT}
    return {
        'was': compare_at_price(now),
        'now': _display_amount(now),
        'currency': currency,
        'off': SALE_OFF_PERCENT,
    }


@register.filter
def youtube_embed_url(url):
    """Convert YouTube URL to embed URL"""
    if not url:
        return None

    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            video_id = video_id.split('?')[0].split('&')[0]
            return f'https://www.youtube.com/embed/{video_id}?playsinline=1&rel=0'

    return None


@register.filter
def is_youtube_url(url):
    if not url:
        return False
    return 'youtube.com' in url or 'youtu.be' in url


@register.filter
def is_bunny_embed_url(url):
    if not url:
        return False
    lower = url.lower()
    return (
        'mediadelivery.net' in lower
        or 'iframe.mediadelivery.net' in lower
        or 'bunny.net/embed' in lower
    )


def normalize_bunny_embed_url(url):
    """Convert Bunny play/share URLs to iframe embed URLs."""
    if not url:
        return None
    # https://player.mediadelivery.net/play/{library}/{video}
    # → https://iframe.mediadelivery.net/embed/{library}/{video}
    play_match = re.search(
        r'(?:player|iframe)\.mediadelivery\.net/(?:play|embed)/([^/\s?#]+)/([^/\s?#]+)',
        url,
        re.IGNORECASE,
    )
    if play_match:
        library_id, video_id = play_match.group(1), play_match.group(2)
        return f'https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay=false&preload=true&playsinline=true'
    if 'iframe.mediadelivery.net' in url.lower() or 'bunny.net/embed' in url.lower():
        if 'playsinline' not in url.lower():
            joiner = '&' if '?' in url else '?'
            return f'{url}{joiner}autoplay=false&playsinline=true'
        return url
    return url


@register.filter
def video_embed_url(url):
    """Return iframe src for YouTube or Bunny Stream embeds."""
    if is_youtube_url(url):
        return youtube_embed_url(url)
    if is_bunny_embed_url(url):
        return normalize_bunny_embed_url(url)
    return None
