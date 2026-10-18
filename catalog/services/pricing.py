from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from catalog.models import Package, PricingTier


TWOPLACES = Decimal('0.01')


def _apply_discount(amount, percent) -> Decimal:
    amount = Decimal(amount)
    percent = Decimal(percent or 0)
    if percent <= 0:
        return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    discounted = amount * (Decimal('1') - (percent / Decimal('100')))
    return max(Decimal('0.00'), discounted).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def resolve_tier_price(tier: PricingTier) -> Decimal:
    """Listed dance-tier price after optional extra discount."""
    return _apply_discount(tier.price, tier.discount_percent)


@dataclass(frozen=True)
class DanceQuote:
    amount: Decimal
    access_duration_days: int
    tier: PricingTier
    video_count: int


def resolve_dance_quote(product, video_count: int) -> DanceQuote:
    """Best price for any number of selected dance videos.

    Uses the 1-video rate times count, unless a larger pack (3 or 6) is cheaper.
    """
    count = int(video_count or 0)
    if count < 1:
        raise ValidationError({'media_asset_ids': 'Select at least one video.'})
    tiers = list(product.active_tiers())
    if not tiers:
        raise ValidationError({'product_id': 'Dance pricing is not configured.'})
    unit = min(tiers, key=lambda tier: (tier.video_count, resolve_tier_price(tier)))
    best_amount = resolve_tier_price(unit) * count
    best_tier = unit
    for tier in tiers:
        price = resolve_tier_price(tier)
        if count <= tier.video_count and price <= best_amount:
            best_amount = price
            best_tier = tier
    return DanceQuote(
        amount=best_amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP),
        access_duration_days=best_tier.access_duration_days,
        tier=best_tier,
        video_count=count,
    )


def resolve_package_price(package: Package) -> Decimal:
    return Decimal(package.individual_price).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def resolve_bundle_price(product) -> Decimal:
    return Decimal(product.bundle_price or 0).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def amount_to_stripe_cents(amount: Decimal) -> int:
    return int((Decimal(amount).quantize(TWOPLACES, rounding=ROUND_HALF_UP) * 100))
