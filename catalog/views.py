from decimal import Decimal

import json
import logging

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from catalog.models import CourseProduct, EntitlementScope, MediaAsset, Package, PricingTier, ProductKind
from catalog.schemas import (
    parse_bundle_checkout_payload,
    parse_dance_checkout_payload,
    parse_package_checkout_payload,
    parse_packages_checkout_payload,
)
from django.urls import reverse
from urllib.parse import urlencode

from catalog.services.access import can_watch_package
from catalog.services.pricing import (
    amount_to_stripe_cents,
    resolve_bundle_price,
    resolve_dance_quote,
    resolve_package_price,
    resolve_tier_price,
)

logger = logging.getLogger(__name__)


def _json_body(request):
    if request.body:
        try:
            return json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            raise ValidationError('Invalid JSON body.')
    return request.POST.dict()


def _error(exc, status=400):
    if hasattr(exc, 'message_dict'):
        return JsonResponse({'ok': False, 'errors': exc.message_dict}, status=status)
    if hasattr(exc, 'messages'):
        return JsonResponse({'ok': False, 'errors': {'__all__': list(exc.messages)}}, status=status)
    return JsonResponse({'ok': False, 'errors': {'__all__': [str(exc)]}}, status=status)


def _product_payload(product, user=None):
    data = {
        'id': product.id,
        'kind': product.kind,
        'title': product.title,
        'slug': product.slug,
        'description': product.description,
        'currency': product.currency,
        'is_active': product.is_active,
    }
    if product.kind == ProductKind.DANCE_VIDEOS:
        data['tiers'] = [
            {
                'id': tier.id,
                'name': tier.name,
                'video_count': tier.video_count,
                'price': str(resolve_tier_price(tier)),
                'list_price': str(tier.price),
                'discount_percent': str(tier.discount_percent),
                'access_duration_days': tier.access_duration_days,
                'access_duration_months': tier.access_duration_months,
            }
            for tier in product.active_tiers()
        ]
        data['videos'] = [
            {
                'id': asset.id,
                'title': asset.title,
                'duration_seconds': asset.duration_seconds,
                'allowed_tier_ids': list(asset.allowed_tiers.values_list('id', flat=True)),
            }
            for asset in product.media_assets.filter(is_active=True).order_by('order', 'id')
        ]
    else:
        data['bundle'] = {
            'enabled': product.bundle_enabled,
            'title': product.bundle_title,
            'price': str(resolve_bundle_price(product)),
            'access_duration_days': product.bundle_access_duration_days,
        }
        data['packages'] = [
            {
                'id': package.id,
                'chapter_number': package.chapter_number,
                'title': package.title,
                'slug': package.slug,
                'description': package.description,
                'price': str(resolve_package_price(package)),
                'access_duration_days': package.access_duration_days,
                'video_count': package.media_assets.filter(is_active=True).count(),
                'cover_url': package.get_cover_url(),
                'has_access': can_watch_package(user, package) if user else False,
            }
            for package in product.active_packages()
        ]
    return data


@require_GET
def product_list(request):
    products = CourseProduct.objects.filter(is_active=True)
    return JsonResponse({
        'ok': True,
        'products': [_product_payload(product, request.user) for product in products],
    })


@require_GET
def product_detail(request, slug):
    product = get_object_or_404(CourseProduct, slug=slug, is_active=True)
    return JsonResponse({'ok': True, 'product': _product_payload(product, request.user)})


def _require_buyer(request):
    if request.user.is_authenticated:
        return None
    next_path = '/'
    try:
        body = json.loads(request.body.decode('utf-8') or '{}')
        cancel = body.get('cancel_path') if isinstance(body, dict) else None
        if isinstance(cancel, str) and cancel.startswith('/'):
            next_path = cancel
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
        pass
    login_url = reverse('users:login') + '?' + urlencode({'next': next_path})
    return JsonResponse(
        {'ok': False, 'error': 'Please log in to buy.', 'login_url': login_url},
        status=401,
    )


def _with_course(product, metadata):
    if getattr(product, 'linked_course_id', None):
        metadata['course_id'] = str(product.linked_course_id)
    return metadata


def _start_stripe_checkout(request, *, name, description, amount, currency, metadata, cancel_path=None):
    if not settings.STRIPE_SECRET_KEY:
        raise ValidationError('Payments are not configured.')
    cents = amount_to_stripe_cents(amount)
    if cents <= 0:
        raise ValidationError('Resolved price must be greater than 0.')
    stripe.api_key = settings.STRIPE_SECRET_KEY
    cancel_url = request.build_absolute_uri(cancel_path or '/courses/')
    metadata = dict(metadata or {})
    metadata['item_name'] = name[:160]
    session_kwargs = {
        'payment_method_types': ['card'],
        'line_items': [{
            'price_data': {
                'currency': (currency or 'eur').lower(),
                'product_data': {
                    'name': name[:120],
                    'description': (description or name)[:500],
                },
                'unit_amount': cents,
            },
            'quantity': 1,
        }],
        'mode': 'payment',
        # Braces must stay raw — Django's build_absolute_uri encodes { } and Stripe then never substitutes.
        'success_url': request.build_absolute_uri('/api/success/') + '?session_id={CHECKOUT_SESSION_ID}',
        'cancel_url': cancel_url,
        'metadata': metadata,
    }
    if request.user.is_authenticated:
        metadata['user_id'] = str(request.user.id)
        if request.user.email:
            session_kwargs['customer_email'] = request.user.email
    session = stripe.checkout.Session.create(**session_kwargs)
    try:
        from users.stats import record_buy_click
        record_buy_click(name, request)
    except Exception:
        pass
    return session


@require_POST
def checkout_dance_tier(request):
    auth_error = _require_buyer(request)
    if auth_error:
        return auth_error
    try:
        payload = parse_dance_checkout_payload(_json_body(request))
        product = get_object_or_404(CourseProduct, pk=payload.product_id, is_active=True, kind=ProductKind.DANCE_VIDEOS)
        assets = list(MediaAsset.objects.filter(pk__in=payload.media_asset_ids, product=product, is_active=True))
        if len(assets) != len(payload.media_asset_ids):
            raise ValidationError({'media_asset_ids': 'One or more videos were not found.'})
        quote = resolve_dance_quote(product, len(assets))
        for asset in assets:
            if not asset.is_allowed_in_tier(quote.tier):
                raise ValidationError({'media_asset_ids': f'"{asset.title}" is not available in this pack.'})
        checkout = _start_stripe_checkout(
            request,
            name=f'{product.title} — {quote.video_count} video(s)',
            description=f'Access to {quote.video_count} selected video(s) for {quote.access_duration_days} days',
            amount=quote.amount,
            currency=product.currency,
            metadata=_with_course(product, {
                'payment_type': 'catalog',
                'scope': EntitlementScope.SELECTED_ASSETS,
                'product_id': str(product.id),
                'tier_id': str(quote.tier.id),
                'media_asset_ids': ','.join(str(a.id) for a in assets),
                'access_duration_days': str(quote.access_duration_days),
            }),
        )
        return JsonResponse({'ok': True, 'checkout_url': checkout.url})
    except stripe.error.StripeError as exc:
        logger.exception('Dance catalog checkout failed')
        return JsonResponse({'ok': False, 'errors': {'__all__': [exc.user_message or str(exc)]}}, status=400)
    except ValidationError as exc:
        return _error(exc)


@require_POST
def checkout_package(request):
    auth_error = _require_buyer(request)
    if auth_error:
        return auth_error
    try:
        raw = _json_body(request)
        payload = parse_package_checkout_payload(raw)
        package = get_object_or_404(
            Package.objects.select_related('product'),
            pk=payload.package_id,
            is_active=True,
            product__is_active=True,
        )
        if can_watch_package(request.user, package):
            raise ValidationError({'package_id': 'You already have access to this chapter.'})
        amount = resolve_package_price(package)
        cancel_path = raw.get('cancel_path') if isinstance(raw, dict) else None
        checkout = _start_stripe_checkout(
            request,
            name=f'{package.product.title} — {package.title}',
            description=package.description or package.title,
            amount=amount,
            currency=package.product.currency,
            metadata=_with_course(package.product, {
                'payment_type': 'catalog',
                'scope': EntitlementScope.PACKAGE,
                'product_id': str(package.product_id),
                'package_id': str(package.id),
            }),
            cancel_path=cancel_path if isinstance(cancel_path, str) and cancel_path.startswith('/') else None,
        )
        return JsonResponse({'ok': True, 'checkout_url': checkout.url})
    except stripe.error.StripeError as exc:
        logger.exception('Package catalog checkout failed')
        return JsonResponse({'ok': False, 'errors': {'__all__': [exc.user_message or str(exc)]}}, status=400)
    except ValidationError as exc:
        return _error(exc)


@require_POST
def checkout_packages(request):
    auth_error = _require_buyer(request)
    if auth_error:
        return auth_error
    try:
        body = _json_body(request)
        payload = parse_packages_checkout_payload(body)
        product = get_object_or_404(
            CourseProduct, pk=payload.product_id, is_active=True, kind=ProductKind.PHYSIO_PACKAGES,
        )
        packages = list(product.packages.filter(pk__in=payload.package_ids, is_active=True))
        if len(packages) != len(payload.package_ids):
            raise ValidationError({'package_ids': 'One or more packages were not found.'})
        cancel_path = body.get('cancel_path') if isinstance(body, dict) else None
        amount = sum((resolve_package_price(pkg) for pkg in packages), start=Decimal('0.00'))
        checkout = _start_stripe_checkout(
            request,
            name=f'{product.title} — {len(packages)} package(s)',
            description=', '.join(pkg.title for pkg in packages)[:500],
            amount=amount,
            currency=product.currency,
            metadata=_with_course(product, {
                'payment_type': 'catalog',
                'scope': EntitlementScope.PACKAGES if len(packages) > 1 else EntitlementScope.PACKAGE,
                'product_id': str(product.id),
                'package_id': str(packages[0].id) if len(packages) == 1 else '',
                'package_ids': ','.join(str(pkg.id) for pkg in packages),
            }),
            cancel_path=cancel_path if isinstance(cancel_path, str) and cancel_path.startswith('/') else None,
        )
        return JsonResponse({'ok': True, 'checkout_url': checkout.url, 'amount': str(amount)})
    except stripe.error.StripeError as exc:
        logger.exception('Packages catalog checkout failed')
        return JsonResponse({'ok': False, 'errors': {'__all__': [exc.user_message or str(exc)]}}, status=400)
    except ValidationError as exc:
        return _error(exc)


@require_POST
def checkout_bundle(request):
    auth_error = _require_buyer(request)
    if auth_error:
        return auth_error
    try:
        payload = parse_bundle_checkout_payload(_json_body(request))
        product = get_object_or_404(
            CourseProduct, pk=payload.product_id, is_active=True, kind=ProductKind.PHYSIO_PACKAGES,
        )
        if not product.bundle_enabled:
            raise ValidationError({'product_id': 'The full bundle is not available.'})
        amount = resolve_bundle_price(product)
        checkout = _start_stripe_checkout(
            request,
            name=product.bundle_title or f'{product.title} bundle',
            description=f'All {product.expected_package_count} packages',
            amount=amount,
            currency=product.currency,
            metadata=_with_course(product, {
                'payment_type': 'catalog',
                'scope': EntitlementScope.FULL_BUNDLE,
                'product_id': str(product.id),
            }),
        )
        return JsonResponse({'ok': True, 'checkout_url': checkout.url})
    except stripe.error.StripeError as exc:
        logger.exception('Bundle catalog checkout failed')
        return JsonResponse({'ok': False, 'errors': {'__all__': [exc.user_message or str(exc)]}}, status=400)
    except ValidationError as exc:
        return _error(exc)


@require_GET
def my_entitlements(request):
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'errors': {'__all__': ['Authentication required.']}}, status=401)
    from catalog.services.access import active_entitlements_qs
    rows = []
    for entitlement in active_entitlements_qs(request.user):
        rows.append({
            'id': entitlement.id,
            'product': entitlement.product.title,
            'scope': entitlement.scope,
            'started_at': entitlement.started_at.isoformat(),
            'expires_at': entitlement.expires_at.isoformat() if entitlement.expires_at else None,
            'remaining_days': entitlement.remaining_days(),
            'is_active': entitlement.is_currently_valid(),
            'media_asset_ids': list(entitlement.media_assets.values_list('id', flat=True)),
            'package_id': entitlement.package_id,
        })
    return JsonResponse({'ok': True, 'entitlements': rows})
