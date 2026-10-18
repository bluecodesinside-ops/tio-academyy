"""Staff AJAX endpoints used by the catalog admin configurators."""
from __future__ import annotations

import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from catalog.models import CourseProduct, MediaAsset, Package, PricingTier, ProductKind
from catalog.schemas import (
    parse_bundle_config_payload,
    parse_chapter_video_map_payload,
    parse_pricing_tier_payload,
)
from courses.models import Session


def _json_body(request):
    if request.content_type and 'application/json' in request.content_type:
        try:
            return json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            raise ValidationError('Invalid JSON body.')
    return request.POST.dict()


def _error_response(exc, status=400):
    if hasattr(exc, 'message_dict'):
        return JsonResponse({'ok': False, 'errors': exc.message_dict}, status=status)
    if hasattr(exc, 'messages'):
        return JsonResponse({'ok': False, 'errors': {'__all__': list(exc.messages)}}, status=status)
    return JsonResponse({'ok': False, 'errors': {'__all__': [str(exc)]}}, status=status)


@require_POST
def save_pricing_tiers(request, product_id):
    product = get_object_or_404(CourseProduct, pk=product_id)
    if product.kind != ProductKind.DANCE_VIDEOS:
        return JsonResponse({'ok': False, 'errors': {'kind': ['Tiers are only for dance products.']}}, status=400)
    try:
        body = _json_body(request)
        rows = body.get('tiers') if isinstance(body, dict) else None
        if not isinstance(rows, list):
            raise ValidationError({'tiers': 'Send a list of tier objects.'})
        payloads = [parse_pricing_tier_payload(row) for row in rows]
        counts = [p.video_count for p in payloads]
        if len(counts) != len(set(counts)):
            raise ValidationError({'video_count': 'Each tier must have a unique video count.'})
    except ValidationError as exc:
        return _error_response(exc)

    keep_ids = []
    for payload in payloads:
        defaults = {
            'name': payload.name,
            'price': payload.price,
            'access_duration_days': payload.access_duration_days,
            'discount_percent': payload.discount_percent,
            'is_active': payload.is_active,
            'display_order': payload.display_order,
            'stripe_price_id': payload.stripe_price_id,
        }
        if payload.id:
            tier = get_object_or_404(PricingTier, pk=payload.id, product=product)
            for field, value in defaults.items():
                setattr(tier, field, value)
            tier.video_count = payload.video_count
            tier.full_clean()
            tier.save()
        else:
            tier = PricingTier(product=product, video_count=payload.video_count, **defaults)
            tier.full_clean()
            tier.save()
        keep_ids.append(tier.pk)

    product.pricing_tiers.exclude(pk__in=keep_ids).delete()
    messages.success(request, 'Pricing tiers saved.')
    return JsonResponse({
        'ok': True,
        'message': 'Pricing tiers saved.',
        'tiers': [
            {
                'id': t.id,
                'name': t.name,
                'video_count': t.video_count,
                'price': str(t.price),
                'access_duration_days': t.access_duration_days,
                'discount_percent': str(t.discount_percent),
                'is_active': t.is_active,
                'display_order': t.display_order,
            }
            for t in product.pricing_tiers.order_by('display_order', 'video_count')
        ],
    })


@require_POST
def save_bundle_config(request, product_id):
    product = get_object_or_404(CourseProduct, pk=product_id)
    try:
        payload = parse_bundle_config_payload(_json_body(request))
    except ValidationError as exc:
        return _error_response(exc)
    product.bundle_enabled = payload.bundle_enabled
    product.bundle_title = payload.bundle_title
    product.bundle_price = payload.bundle_price
    product.bundle_access_duration_days = payload.bundle_access_duration_days
    product.expected_package_count = payload.expected_package_count
    product.full_clean()
    product.save(update_fields=[
        'bundle_enabled',
        'bundle_title',
        'bundle_price',
        'bundle_access_duration_days',
        'expected_package_count',
        'updated_at',
    ])
    messages.success(request, 'Bundle configuration saved.')
    return JsonResponse({
        'ok': True,
        'message': 'Bundle configuration saved.',
        'bundle': {
            'bundle_enabled': product.bundle_enabled,
            'bundle_title': product.bundle_title,
            'bundle_price': str(product.bundle_price),
            'bundle_access_duration_days': product.bundle_access_duration_days,
            'expected_package_count': product.expected_package_count,
            'package_count': product.packages.filter(is_active=True).count(),
        },
    })


@require_POST
def map_chapter_videos(request, package_id):
    package = get_object_or_404(Package.objects.select_related('product'), pk=package_id)
    try:
        body = _json_body(request)
        body.setdefault('package_id', package.pk)
        payload = parse_chapter_video_map_payload(body)
    except ValidationError as exc:
        return _error_response(exc)

    product = package.product
    keep_ids = []

    if payload.media_asset_ids:
        assets = list(MediaAsset.objects.filter(pk__in=payload.media_asset_ids, product=product))
        if len(assets) != len(payload.media_asset_ids):
            return JsonResponse({'ok': False, 'errors': {'media_asset_ids': ['One or more videos were not found.']}}, status=400)
        MediaAsset.objects.filter(pk__in=payload.media_asset_ids).update(package=package)
        keep_ids.extend(payload.media_asset_ids)

    for session_id in payload.session_ids:
        session = Session.objects.filter(pk=session_id).first()
        if not session:
            continue
        asset, _ = MediaAsset.objects.get_or_create(
            product=product,
            session=session,
            defaults={
                'package': package,
                'title': session.title,
                'description': session.description or '',
                'video_url': session.video_url or '',
                'duration_seconds': (session.duration or 0) * 60,
                'order': session.order or 0,
                'is_active': session.is_active,
            },
        )
        if asset.package_id != package.pk:
            asset.package = package
            asset.save(update_fields=['package', 'updated_at'])
        keep_ids.append(asset.pk)

    # Dance videos may be ungrouped. Physio videos can sit unassigned until you place them.
    if 'media_asset_ids' in body or 'session_ids' in body:
        package.media_assets.exclude(pk__in=keep_ids).update(package=None)

    messages.success(request, f'Videos mapped to {package.title}.')
    return JsonResponse({
        'ok': True,
        'message': f'Videos mapped to {package.title}.',
        'assets': [
            {'id': a.id, 'title': a.title, 'session_id': a.session_id, 'order': a.order}
            for a in package.media_assets.filter(is_active=True).order_by('order', 'id')
        ],
    })


@require_POST
def save_physio_layout(request, product_id):
    """Save package prices/titles and which course video belongs to which package."""
    product = get_object_or_404(CourseProduct, pk=product_id, kind=ProductKind.PHYSIO_PACKAGES)
    try:
        body = _json_body(request)
        rows = body.get('packages') if isinstance(body, dict) else None
        assignments = body.get('assignments') if isinstance(body, dict) else None
        if not isinstance(rows, list):
            raise ValidationError({'packages': 'Send the 15 packages.'})
        if not isinstance(assignments, list):
            assignments = []
        package_ids = set(product.packages.values_list('id', flat=True))
        for row in rows:
            if not isinstance(row, dict):
                continue
            pkg_id = int(row.get('id') or 0)
            if pkg_id not in package_ids:
                continue
            package = Package.objects.get(pk=pkg_id, product=product)
            title = (row.get('title') or '').strip() or package.title
            price = row.get('individual_price')
            package.title = title[:200]
            if price not in (None, ''):
                from decimal import Decimal
                amount = Decimal(str(price))
                if amount <= 0:
                    raise ValidationError({'individual_price': f'{package.title} needs a price greater than 0.'})
                package.individual_price = amount
            package.full_clean()
            package.save()
        MediaAsset.objects.filter(product=product).update(package=None)
        for item in assignments:
            if not isinstance(item, dict):
                continue
            package_id = int(item.get('package_id') or 0)
            session_id = int(item.get('session_id') or 0)
            if package_id not in package_ids or not session_id:
                continue
            package = Package.objects.get(pk=package_id, product=product)
            session = Session.objects.filter(pk=session_id).first()
            if not session:
                continue
            asset, _ = MediaAsset.objects.get_or_create(
                product=product,
                session=session,
                defaults={
                    'package': package,
                    'title': session.title,
                    'description': session.description or '',
                    'video_url': session.video_url or '',
                    'duration_seconds': (session.duration or 0) * 60,
                    'order': session.order or 0,
                    'is_active': session.is_active,
                },
            )
            if asset.package_id != package.id:
                asset.package = package
                asset.save(update_fields=['package', 'updated_at'])
    except (ValidationError, ValueError, TypeError) as exc:
        if isinstance(exc, ValidationError):
            return _error_response(exc)
        return JsonResponse({'ok': False, 'errors': {'__all__': [str(exc)]}}, status=400)

    messages.success(request, 'Physio packages and video placement saved.')
    return JsonResponse({'ok': True, 'message': 'Packages and video placement saved.'})
