"""Grant, expire, and evaluate time-bound catalog entitlements."""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from catalog.models import (
    CourseProduct,
    EntitlementScope,
    MediaAsset,
    Package,
    PricingTier,
    ProductKind,
    UserAccessEntitlement,
)
from catalog.services.pricing import resolve_bundle_price, resolve_dance_quote, resolve_package_price

logger = logging.getLogger(__name__)


def _now():
    return timezone.now()


def _get_or_create_from_stripe(user, product, stripe_session_id, defaults):
    if stripe_session_id:
        existing = UserAccessEntitlement.objects.filter(stripe_session_id=stripe_session_id).first()
        if existing:
            return existing, False
    entitlement = UserAccessEntitlement.objects.create(
        user=user,
        product=product,
        stripe_session_id=stripe_session_id or '',
        **defaults,
    )
    return entitlement, True


def models_q_expiry(now):
    return Q(expires_at__isnull=True) | Q(expires_at__gt=now)


def active_entitlements_qs(user, product=None, at=None):
    if not getattr(user, 'is_authenticated', False):
        return UserAccessEntitlement.objects.none()
    now = at or _now()
    qs = UserAccessEntitlement.objects.filter(
        user=user, is_active=True, started_at__lte=now,
    ).filter(models_q_expiry(now))
    if product is not None:
        qs = qs.filter(product=product)
    return qs.select_related('product', 'pricing_tier', 'package').prefetch_related('media_assets')


def grant_dance_tier(*, user, tier: PricingTier, media_assets, stripe_session_id='', amount=None, granted_by=None, notes='', duration_days=None):
    assets = list(media_assets)
    if not assets:
        raise ValidationError({'media_asset_ids': 'Select at least one video.'})
    for asset in assets:
        if asset.product_id != tier.product_id:
            raise ValidationError({'media_asset_ids': f'"{asset.title}" does not belong to this product.'})
        if not asset.is_allowed_in_tier(tier):
            raise ValidationError({'media_asset_ids': f'"{asset.title}" is not mapped to this tier.'})

    quote = resolve_dance_quote(tier.product, len(assets))
    access_days = duration_days if duration_days is not None else quote.access_duration_days
    started = _now()
    defaults = {
        'pricing_tier': quote.tier,
        'package': None,
        'scope': EntitlementScope.SELECTED_ASSETS,
        'started_at': started,
        'expires_at': UserAccessEntitlement.compute_expiry(started, access_days),
        'is_active': True,
        'amount_paid': amount if amount is not None else quote.amount,
        'currency': tier.product.currency,
        'granted_by': granted_by,
        'notes': notes,
    }
    with transaction.atomic():
        entitlement, created = _get_or_create_from_stripe(user, tier.product, stripe_session_id, defaults)
        if created:
            entitlement.media_assets.set(assets)
        return entitlement


def grant_package(*, user, package: Package, stripe_session_id='', amount=None, granted_by=None, notes='', duration_days=None):
    started = _now()
    days = package.access_duration_days if duration_days is None else duration_days
    defaults = {
        'pricing_tier': None,
        'package': package,
        'scope': EntitlementScope.PACKAGE,
        'started_at': started,
        'expires_at': UserAccessEntitlement.compute_expiry(started, days),
        'is_active': True,
        'amount_paid': amount if amount is not None else resolve_package_price(package),
        'currency': package.product.currency,
        'granted_by': granted_by,
        'notes': notes,
    }
    with transaction.atomic():
        entitlement, created = _get_or_create_from_stripe(user, package.product, stripe_session_id, defaults)
        if created:
            entitlement.media_assets.set(package.media_assets.filter(is_active=True))
        return entitlement


def grant_bundle(*, user, product: CourseProduct, stripe_session_id='', amount=None, granted_by=None, notes=''):
    if not product.bundle_enabled:
        raise ValidationError({'product_id': 'The full bundle is not enabled for this product.'})
    started = _now()
    defaults = {
        'pricing_tier': None,
        'package': None,
        'scope': EntitlementScope.FULL_BUNDLE,
        'started_at': started,
        'expires_at': UserAccessEntitlement.compute_expiry(started, product.bundle_access_duration_days),
        'is_active': True,
        'amount_paid': amount if amount is not None else resolve_bundle_price(product),
        'currency': product.currency,
        'granted_by': granted_by,
        'notes': notes,
    }
    with transaction.atomic():
        entitlement, created = _get_or_create_from_stripe(user, product, stripe_session_id, defaults)
        if created:
            entitlement.media_assets.set(product.media_assets.filter(is_active=True))
            entitlement.packages.set(product.packages.filter(is_active=True))
        return entitlement


def grant_selected_packages(*, user, product, packages, stripe_session_id='', amount=None, granted_by=None, notes=''):
    selected = list(packages)
    if not selected:
        raise ValidationError({'package_ids': 'Select at least one package.'})
    if any(pkg.product_id != product.id for pkg in selected):
        raise ValidationError({'package_ids': 'Packages must belong to the same course.'})
    duration = max((pkg.access_duration_days or 0) for pkg in selected)
    started = _now()
    defaults = {
        'pricing_tier': None,
        'package': selected[0] if len(selected) == 1 else None,
        'scope': EntitlementScope.PACKAGE if len(selected) == 1 else EntitlementScope.PACKAGES,
        'started_at': started,
        'expires_at': UserAccessEntitlement.compute_expiry(started, duration),
        'is_active': True,
        'amount_paid': amount if amount is not None else sum(
            (resolve_package_price(pkg) for pkg in selected), start=Decimal('0.00')
        ),
        'currency': product.currency,
        'granted_by': granted_by,
        'notes': notes,
    }
    with transaction.atomic():
        entitlement, created = _get_or_create_from_stripe(user, product, stripe_session_id, defaults)
        if created:
            entitlement.packages.set(selected)
            entitlement.media_assets.set(
                MediaAsset.objects.filter(package__in=selected, is_active=True)
            )
        return entitlement


def can_watch_asset(user, asset: MediaAsset, at=None) -> bool:
    if not asset or not asset.is_active:
        return False
    if not getattr(user, 'is_authenticated', False):
        return False
    now = at or _now()
    qs = UserAccessEntitlement.objects.filter(
        user=user,
        product=asset.product,
        is_active=True,
        started_at__lte=now,
    ).filter(models_q_expiry(now))

    if qs.filter(scope=EntitlementScope.FULL_BUNDLE).exists():
        return True
    if asset.package_id and qs.filter(scope=EntitlementScope.PACKAGE, package_id=asset.package_id).exists():
        return True
    if asset.package_id and qs.filter(scope=EntitlementScope.PACKAGES, packages=asset.package).exists():
        return True
    if qs.filter(scope=EntitlementScope.SELECTED_ASSETS, media_assets=asset).exists():
        return True
    return False


def can_watch_package(user, package: Package, at=None) -> bool:
    if not package or not package.is_active:
        return False
    if not getattr(user, 'is_authenticated', False):
        return False
    now = at or _now()
    qs = UserAccessEntitlement.objects.filter(
        user=user,
        product=package.product,
        is_active=True,
        started_at__lte=now,
    ).filter(models_q_expiry(now))
    return (
        qs.filter(scope=EntitlementScope.FULL_BUNDLE).exists()
        or qs.filter(scope=EntitlementScope.PACKAGE, package=package).exists()
        or qs.filter(scope=EntitlementScope.PACKAGES, packages=package).exists()
    )


def can_watch_session(user, session, at=None) -> bool:
    """True if any mapped MediaAsset for this Session is covered by a live entitlement."""
    if session is None:
        return False
    assets = list(getattr(session, 'catalog_assets', MediaAsset.objects.none()).filter(is_active=True))
    if not assets:
        assets = list(MediaAsset.objects.filter(session=session, is_active=True))
    if any(can_watch_asset(user, asset, at=at) for asset in assets):
        return True
    packet = getattr(session, 'packet', None)
    if packet is not None:
        try:
            package = packet.catalog_package
        except Exception:
            package = None
        if package is None:
            package = Package.objects.filter(course_packet=packet).first()
        if package and can_watch_package(user, package, at=at):
            return True
    return False


def expire_stale_entitlements(at=None) -> int:
    now = at or _now()
    return UserAccessEntitlement.objects.filter(
        is_active=True,
        expires_at__isnull=False,
        expires_at__lte=now,
    ).update(is_active=False)


def grant_from_stripe_session(session, user=None):
    """Idempotently grant a catalog entitlement from a paid Stripe Checkout session."""
    metadata = getattr(session, 'metadata', None) or (session.get('metadata') if isinstance(session, dict) else {}) or {}
    payment_type = metadata.get('payment_type')
    if payment_type != 'catalog':
        return None

    payment_status = getattr(session, 'payment_status', None) or (session.get('payment_status') if isinstance(session, dict) else None)
    if payment_status not in ('paid', 'no_payment_required'):
        return None

    session_id = getattr(session, 'id', None) or (session.get('id') if isinstance(session, dict) else None) or ''
    existing = UserAccessEntitlement.objects.filter(stripe_session_id=session_id).first() if session_id else None
    if existing:
        return existing

    if user is None:
        return None

    amount_total = getattr(session, 'amount_total', None) or (session.get('amount_total') if isinstance(session, dict) else 0) or 0
    amount = (Decimal(str(amount_total or 0)) / Decimal('100'))
    scope = metadata.get('scope')

    try:
        if scope == EntitlementScope.SELECTED_ASSETS:
            ids = [int(x) for x in (metadata.get('media_asset_ids') or '').split(',') if x.strip()]
            product = CourseProduct.objects.get(pk=int(metadata.get('product_id')))
            assets = list(MediaAsset.objects.filter(pk__in=ids, product=product))
            quote = resolve_dance_quote(product, len(assets))
            duration = metadata.get('access_duration_days')
            return grant_dance_tier(
                user=user,
                tier=quote.tier,
                media_assets=assets,
                stripe_session_id=session_id,
                amount=amount,
                duration_days=int(duration) if duration else quote.access_duration_days,
            )
        if scope == EntitlementScope.PACKAGE:
            package = Package.objects.select_related('product').get(pk=int(metadata.get('package_id')))
            return grant_package(
                user=user,
                package=package,
                stripe_session_id=session_id,
                amount=amount,
            )
        if scope == EntitlementScope.FULL_BUNDLE:
            product = CourseProduct.objects.get(pk=int(metadata.get('product_id')))
            return grant_bundle(
                user=user,
                product=product,
                stripe_session_id=session_id,
                amount=amount,
            )
        if scope in (EntitlementScope.PACKAGES, 'packages'):
            product = CourseProduct.objects.get(pk=int(metadata.get('product_id')))
            ids = [int(x) for x in (metadata.get('package_ids') or '').split(',') if x.strip()]
            packages = list(Package.objects.filter(pk__in=ids, product=product))
            return grant_selected_packages(
                user=user,
                product=product,
                packages=packages,
                stripe_session_id=session_id,
                amount=amount,
            )
    except (PricingTier.DoesNotExist, Package.DoesNotExist, CourseProduct.DoesNotExist, ValueError, ValidationError):
        logger.exception('Failed to grant catalog entitlement for session %s', session_id)
        return None
    logger.warning('Unknown catalog scope=%s for session %s', scope, session_id)
    return None
