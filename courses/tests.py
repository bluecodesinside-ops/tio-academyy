from decimal import Decimal

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from courses.models import Course, Packet, Session
from courses.templatetags.course_extras import compare_at_price
from payments.views import check_session_access


class SalePriceTests(TestCase):
    def test_listed_price_is_seventy_percent_off(self):
        self.assertEqual(compare_at_price(Decimal('39')), Decimal('130'))
        self.assertEqual(compare_at_price(Decimal('19.50')), Decimal('65'))


class FreePreviewPacketTests(TestCase):
    def test_free_preview_is_open_on_packet_course(self):
        course = Course.objects.create(title='Fizio', sell_as_packets=True, price=0)
        packet = Packet.objects.create(course=course, title='Spine', price=Decimal('39'))
        session = Session.objects.create(
            course=course,
            packet=packet,
            title='Preview',
            is_free_preview=True,
            duration=5,
        )

        self.assertTrue(check_session_access(AnonymousUser(), session, course))

    def test_only_one_free_preview_per_packet(self):
        course = Course.objects.create(title='Fizio', sell_as_packets=True, price=0)
        packet = Packet.objects.create(course=course, title='Spine', price=Decimal('39'))
        preview = Session.objects.create(
            course=course, packet=packet, title='Free Preview',
            is_free_preview=True, duration=5, order=0,
        )
        exercise = Session.objects.create(
            course=course, packet=packet, title='Exercise',
            is_free_preview=False, duration=8, order=1,
        )
        anon = AnonymousUser()
        self.assertTrue(check_session_access(anon, preview, course))
        self.assertFalse(check_session_access(anon, exercise, course))
