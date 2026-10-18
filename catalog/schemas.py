"""
Payload schemas and input validation for catalog admin forms and API routes.

Python equivalent of typed Zod/Yup schemas: parse untrusted dicts into
frozen dataclasses or raise django.core.exceptions.ValidationError.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from django.core.exceptions import ValidationError

from catalog.models import months_to_days


def _as_dict(data: Any) -> dict:
    if not isinstance(data, Mapping):
        raise ValidationError('Expected a JSON object.')
    return dict(data)


def _require_str(value: Any, field: str, *, max_length: int = 200, allow_blank: bool = False) -> str:
    if value is None:
        value = ''
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    if not text and not allow_blank:
        raise ValidationError({field: 'This field is required.'})
    if len(text) > max_length:
        raise ValidationError({field: f'Must be at most {max_length} characters.'})
    return text


def _require_int(value: Any, field: str, *, min_value: int | None = None, max_value: int | None = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError({field: 'Must be a whole number.'})
    if min_value is not None and number < min_value:
        raise ValidationError({field: f'Must be at least {min_value}.'})
    if max_value is not None and number > max_value:
        raise ValidationError({field: f'Must be at most {max_value}.'})
    return number


def _require_decimal(value: Any, field: str, *, min_value: Decimal = Decimal('0')) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError({field: 'Must be a valid amount.'})
    if amount < min_value:
        raise ValidationError({field: f'Must be at least {min_value}.'})
    return amount.quantize(Decimal('0.01'))


def _require_bool(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (1, '1', 'true', 'True', 'on', 'yes'):
        return True
    if value in (0, '0', 'false', 'False', 'off', 'no', '', None):
        return False
    raise ValidationError({field: 'Must be true or false.'})


def _require_id_list(value: Any, field: str) -> list[int]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(',') if p.strip()]
        value = parts
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValidationError({field: 'Must be a list of ids.'})
    ids = []
    seen = set()
    for item in value:
        number = _require_int(item, field, min_value=1)
        if number not in seen:
            ids.append(number)
            seen.add(number)
    return ids


def _duration_days(data: Mapping[str, Any], default_days: int | None = None) -> int:
    if data.get('access_duration_days') not in (None, ''):
        return _require_int(data.get('access_duration_days'), 'access_duration_days', min_value=0)
    if data.get('access_duration_months') not in (None, ''):
        months = _require_int(data.get('access_duration_months'), 'access_duration_months', min_value=0)
        return months_to_days(months)
    if default_days is not None:
        return default_days
    raise ValidationError({'access_duration_days': 'Provide access duration in days or months.'})


@dataclass(frozen=True)
class PricingTierPayload:
    name: str
    video_count: int
    price: Decimal
    access_duration_days: int
    discount_percent: Decimal
    is_active: bool
    display_order: int
    stripe_price_id: str
    id: int | None = None


def parse_pricing_tier_payload(data: Any) -> PricingTierPayload:
    data = _as_dict(data)
    errors: dict[str, str] = {}
    try:
        name = _require_str(data.get('name'), 'name', max_length=100)
    except ValidationError as exc:
        errors.update(exc.message_dict if hasattr(exc, 'message_dict') else {'name': str(exc)})
        name = ''
    try:
        video_count = _require_int(data.get('video_count'), 'video_count', min_value=1, max_value=50)
    except ValidationError as exc:
        errors.update(exc.message_dict)
        video_count = 1
    try:
        price = _require_decimal(data.get('price'), 'price', min_value=Decimal('0.01'))
    except ValidationError as exc:
        errors.update(exc.message_dict)
        price = Decimal('0.00')
    try:
        duration = _duration_days(data)
        if duration <= 0:
            raise ValidationError({'access_duration_days': 'Dance tiers need a duration greater than 0.'})
    except ValidationError as exc:
        errors.update(exc.message_dict)
        duration = 30
    try:
        discount = _require_decimal(data.get('discount_percent') or 0, 'discount_percent')
        if discount > Decimal('100'):
            raise ValidationError({'discount_percent': 'Must be at most 100.'})
    except ValidationError as exc:
        errors.update(exc.message_dict)
        discount = Decimal('0')
    try:
        is_active = _require_bool(data.get('is_active', True), 'is_active')
        display_order = _require_int(data.get('display_order') or 0, 'display_order', min_value=0)
        stripe_price_id = _require_str(data.get('stripe_price_id') or '', 'stripe_price_id', max_length=200, allow_blank=True)
        pk = data.get('id')
        parsed_id = _require_int(pk, 'id', min_value=1) if pk not in (None, '') else None
    except ValidationError as exc:
        errors.update(exc.message_dict)
        is_active, display_order, stripe_price_id, parsed_id = True, 0, '', None
    if errors:
        raise ValidationError(errors)
    return PricingTierPayload(
        id=parsed_id,
        name=name,
        video_count=video_count,
        price=price,
        access_duration_days=duration,
        discount_percent=discount,
        is_active=is_active,
        display_order=display_order,
        stripe_price_id=stripe_price_id,
    )


@dataclass(frozen=True)
class BundleConfigPayload:
    bundle_enabled: bool
    bundle_title: str
    bundle_price: Decimal
    bundle_access_duration_days: int
    expected_package_count: int


def parse_bundle_config_payload(data: Any) -> BundleConfigPayload:
    data = _as_dict(data)
    enabled = _require_bool(data.get('bundle_enabled', False), 'bundle_enabled')
    title = _require_str(data.get('bundle_title') or 'All 15 Packages', 'bundle_title', max_length=200, allow_blank=True)
    price = _require_decimal(data.get('bundle_price') or 0, 'bundle_price')
    duration = _duration_days(data, default_days=365)
    expected = _require_int(data.get('expected_package_count') or 15, 'expected_package_count', min_value=1, max_value=50)
    if enabled and price <= 0:
        raise ValidationError({'bundle_price': 'Bundle price must be greater than 0 when enabled.'})
    return BundleConfigPayload(
        bundle_enabled=enabled,
        bundle_title=title or 'All 15 Packages',
        bundle_price=price,
        bundle_access_duration_days=duration,
        expected_package_count=expected,
    )


@dataclass(frozen=True)
class ChapterVideoMapPayload:
    package_id: int
    media_asset_ids: list[int]
    session_ids: list[int]


def parse_chapter_video_map_payload(data: Any) -> ChapterVideoMapPayload:
    data = _as_dict(data)
    return ChapterVideoMapPayload(
        package_id=_require_int(data.get('package_id'), 'package_id', min_value=1),
        media_asset_ids=_require_id_list(data.get('media_asset_ids'), 'media_asset_ids'),
        session_ids=_require_id_list(data.get('session_ids'), 'session_ids'),
    )


@dataclass(frozen=True)
class DanceCheckoutPayload:
    product_id: int
    media_asset_ids: list[int]
    tier_id: int | None = None


def parse_dance_checkout_payload(data: Any) -> DanceCheckoutPayload:
    data = _as_dict(data)
    ids = _require_id_list(data.get('media_asset_ids'), 'media_asset_ids')
    if not ids:
        raise ValidationError({'media_asset_ids': 'Select at least one video.'})
    raw_tier = data.get('tier_id')
    tier_id = None
    if raw_tier not in (None, '', 0, '0'):
        tier_id = _require_int(raw_tier, 'tier_id', min_value=1)
    return DanceCheckoutPayload(
        product_id=_require_int(data.get('product_id'), 'product_id', min_value=1),
        media_asset_ids=ids,
        tier_id=tier_id,
    )


@dataclass(frozen=True)
class PackageCheckoutPayload:
    package_id: int


def parse_package_checkout_payload(data: Any) -> PackageCheckoutPayload:
    data = _as_dict(data)
    return PackageCheckoutPayload(
        package_id=_require_int(data.get('package_id'), 'package_id', min_value=1),
    )


@dataclass(frozen=True)
class PackagesCheckoutPayload:
    product_id: int
    package_ids: list[int]


def parse_packages_checkout_payload(data: Any) -> PackagesCheckoutPayload:
    data = _as_dict(data)
    ids = _require_id_list(data.get('package_ids'), 'package_ids')
    if not ids:
        raise ValidationError({'package_ids': 'Select at least one package.'})
    return PackagesCheckoutPayload(
        product_id=_require_int(data.get('product_id'), 'product_id', min_value=1),
        package_ids=ids,
    )


@dataclass(frozen=True)
class BundleCheckoutPayload:
    product_id: int


def parse_bundle_checkout_payload(data: Any) -> BundleCheckoutPayload:
    data = _as_dict(data)
    return BundleCheckoutPayload(
        product_id=_require_int(data.get('product_id'), 'product_id', min_value=1),
    )
