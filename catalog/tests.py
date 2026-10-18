from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import (
    CourseProduct,
    MediaAsset,
    Package,
    PricingTier,
    ProductKind,
)
from catalog.schemas import parse_dance_checkout_payload, parse_pricing_tier_payload
from catalog.seed import seed_catalog
from catalog.services.access import (
    can_watch_asset,
    can_watch_package,
    grant_bundle,
    grant_dance_tier,
    grant_package,
)
from catalog.services.pricing import resolve_dance_quote, resolve_tier_price


class SchemaValidationTests(TestCase):
    def test_tier_payload_accepts_months(self):
        payload = parse_pricing_tier_payload({
            'name': '3 Videos',
            'video_count': 3,
            'price': '39.00',
            'access_duration_months': 2,
            'discount_percent': '0',
            'is_active': True,
            'display_order': 1,
        })
        self.assertEqual(payload.access_duration_days, 60)
        self.assertEqual(payload.price, Decimal('39.00'))

    def test_tier_payload_rejects_zero_price(self):
        with self.assertRaises(ValidationError) as ctx:
            parse_pricing_tier_payload({
                'name': '1 Video',
                'video_count': 1,
                'price': '0',
                'access_duration_days': 30,
            })
        self.assertIn('price', ctx.exception.message_dict)

    def test_dance_checkout_requires_videos(self):
        with self.assertRaises(ValidationError):
            parse_dance_checkout_payload({'product_id': 1, 'tier_id': 1, 'media_asset_ids': []})


class PricingServiceTests(TestCase):
    def setUp(self):
        self.product = CourseProduct.objects.create(
            kind=ProductKind.DANCE_VIDEOS,
            title='Dance',
            slug='dance-test',
        )
        self.tier = PricingTier.objects.create(
            product=self.product,
            name='3 Videos',
            video_count=3,
            price=Decimal('39.00'),
            access_duration_days=60,
            discount_percent=Decimal('10.00'),
        )

    def test_discount_is_applied(self):
        self.assertEqual(resolve_tier_price(self.tier), Decimal('35.10'))


class EntitlementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('dancer', 'dancer@example.com', 'pass')
        self.product = CourseProduct.objects.create(
            kind=ProductKind.DANCE_VIDEOS,
            title='Dance',
            slug='dance-entitlement',
        )
        self.tier = PricingTier.objects.create(
            product=self.product,
            name='1 Video',
            video_count=1,
            price=Decimal('17.00'),
            access_duration_days=30,
        )
        self.asset = MediaAsset.objects.create(
            product=self.product,
            title='Video A',
            video_url='https://example.com/a.mp4',
        )

    def test_dance_grant_allows_any_selected_videos(self):
        extra = MediaAsset.objects.create(
            product=self.product,
            title='Video B',
            video_url='https://example.com/b.mp4',
        )
        entitlement = grant_dance_tier(user=self.user, tier=self.tier, media_assets=[self.asset, extra])
        self.assertTrue(can_watch_asset(self.user, self.asset))
        self.assertTrue(can_watch_asset(self.user, extra))
        self.assertEqual(entitlement.amount_paid, Decimal('34.00'))

    def test_dance_grant_unlocks_asset_until_expiry(self):
        entitlement = grant_dance_tier(user=self.user, tier=self.tier, media_assets=[self.asset])
        self.assertTrue(entitlement.is_currently_valid())
        self.assertTrue(can_watch_asset(self.user, self.asset))
        entitlement.expires_at = timezone.now() - timedelta(seconds=1)
        entitlement.save(update_fields=['expires_at'])
        self.assertFalse(entitlement.is_currently_valid())
        self.assertFalse(can_watch_asset(self.user, self.asset))

    def test_physio_package_and_bundle(self):
        physio = CourseProduct.objects.create(
            kind=ProductKind.PHYSIO_PACKAGES,
            title='Physio',
            slug='physio-test',
            bundle_enabled=True,
            bundle_price=Decimal('199.00'),
            bundle_access_duration_days=365,
            expected_package_count=15,
        )
        chapter = Package.objects.create(
            product=physio,
            title='Chapter 1',
            slug='ch-1',
            chapter_number=1,
            individual_price=Decimal('19.00'),
            access_duration_days=90,
        )
        video = MediaAsset.objects.create(
            product=physio,
            package=chapter,
            title='Rehab 1',
            video_url='https://example.com/rehab.mp4',
        )
        grant_package(user=self.user, package=chapter)
        self.assertTrue(can_watch_package(self.user, chapter))
        self.assertTrue(can_watch_asset(self.user, video))

        other = Package.objects.create(
            product=physio,
            title='Chapter 2',
            slug='ch-2',
            chapter_number=2,
            individual_price=Decimal('19.00'),
        )
        self.assertFalse(can_watch_package(self.user, other))

        grant_bundle(user=self.user, product=physio, stripe_session_id='cs_test_bundle')
        self.assertTrue(can_watch_package(self.user, other))


class PurchasedVideoOpensTests(TestCase):
    """A paying student must always be handed a clickable route to what they bought."""

    @classmethod
    def setUpTestData(cls):
        from courses.models import Course, Session
        cls.user = User.objects.create_user('buyer', 'buyer@example.com', 'pass')
        cls.course = Course.objects.create(title='Dance course', price=Decimal('64.00'))
        cls.dance = CourseProduct.objects.create(
            kind=ProductKind.DANCE_VIDEOS,
            title='Dance videos',
            slug='dance-open-test',
            linked_course=cls.course,
            bundle_enabled=True,
            bundle_price=Decimal('64.00'),
            bundle_access_duration_days=120,
        )
        cls.tier = PricingTier.objects.create(
            product=cls.dance, name='1 Video', video_count=1,
            price=Decimal('17.00'), access_duration_days=30,
        )
        cls.session = Session.objects.create(
            course=cls.course, title='Kukes Dance', order=1,
            video_url='https://example.com/kukes.mp4',
        )
        cls.asset = MediaAsset.objects.create(
            product=cls.dance, session=cls.session, title='Kukes Dance',
            video_url='https://example.com/kukes.mp4',
        )

    def page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('course_detail', args=[self.course.id]))
        return response.content.decode('utf-8')

    def assert_video_opens(self):
        html = self.page()
        link = f'/?session={self.session.id}'
        self.assertIn(f'href="/course/{self.course.id}{link}', html)
        self.assertIn(f"window.location.href='/course/{self.course.id}{link}'", html)
        response = self.client.get(
            reverse('course_detail', args=[self.course.id]), {'session': self.session.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('kukes.mp4', response.content.decode('utf-8'))

    def test_unpaid_video_stays_unopenable(self):
        self.assertNotIn(f'?session={self.session.id}', self.page())

    def test_dance_tier_purchase_opens_the_video(self):
        grant_dance_tier(user=self.user, tier=self.tier, media_assets=[self.asset])
        self.assert_video_opens()

    def test_dance_bundle_purchase_opens_the_video(self):
        grant_bundle(user=self.user, product=self.dance, stripe_session_id='cs_test_open')
        self.assert_video_opens()

    def test_physio_package_purchase_opens_the_video(self):
        from catalog.services.sync import sync_course_packet
        from courses.models import Packet
        packet = Packet.objects.create(
            course=self.course, title='Chapter 1', order=1, price=Decimal('19.00'),
        )
        self.session.packet = packet
        self.session.save(update_fields=['packet'])
        chapter = sync_course_packet(packet)
        grant_package(user=self.user, package=chapter)
        self.client.force_login(self.user)
        response = self.client.get(reverse('packet_detail', args=[self.course.id, packet.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'?session={self.session.id}', response.content.decode('utf-8'))


class SeedAndApiTests(TestCase):
    def test_seed_creates_expected_catalog(self):
        seed_catalog()
        seed_catalog()  # idempotent
        dance = CourseProduct.objects.get(slug='traditional-dance-videos')
        physio = CourseProduct.objects.get(slug='physiotherapy-packages')
        self.assertEqual(dance.pricing_tiers.count(), 3)
        self.assertEqual(physio.packages.count(), 15)
        one = dance.pricing_tiers.get(video_count=1)
        self.assertEqual(one.price, Decimal('17.00'))
        self.assertEqual(one.access_duration_days, 30)
        six = dance.pricing_tiers.get(video_count=6)
        self.assertEqual(six.price, Decimal('64.00'))
        self.assertEqual(six.access_duration_days, 120)

    def test_product_list_api(self):
        seed_catalog()
        response = self.client.get('/api/catalog/products/')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['ok'])
        kinds = {item['kind'] for item in body['products']}
        self.assertEqual(kinds, {ProductKind.DANCE_VIDEOS, ProductKind.PHYSIO_PACKAGES})

    def test_dance_quote_picks_best_pack_or_per_video(self):
        seed_catalog()
        product = CourseProduct.objects.get(slug='traditional-dance-videos')
        one = resolve_dance_quote(product, 1)
        two = resolve_dance_quote(product, 2)
        three = resolve_dance_quote(product, 3)
        four = resolve_dance_quote(product, 4)
        six = resolve_dance_quote(product, 6)
        self.assertEqual(one.amount, Decimal('17.00'))
        self.assertEqual(two.amount, Decimal('34.00'))
        self.assertEqual(three.amount, Decimal('39.00'))
        self.assertEqual(four.amount, Decimal('64.00'))
        self.assertEqual(six.amount, Decimal('64.00'))

    def test_dance_checkout_payload_allows_any_count(self):
        payload = parse_dance_checkout_payload({
            'product_id': 1,
            'media_asset_ids': [10, 11],
        })
        self.assertEqual(payload.media_asset_ids, [10, 11])
        self.assertIsNone(payload.tier_id)

    def test_packages_checkout_requires_login(self):
        seed_catalog()
        product = CourseProduct.objects.get(slug='physiotherapy-packages')
        package = product.packages.first()
        response = self.client.post(
            '/api/catalog/checkout/packages/',
            data={'product_id': product.id, 'package_ids': [package.id]},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('login_url', response.json())
