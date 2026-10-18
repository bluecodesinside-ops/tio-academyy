from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import EntitlementScope, UserAccessEntitlement
from courses.models import Course, Packet
from users.models import UserProfile


class AuthPagesTests(TestCase):
    def test_login_is_simple_and_has_profile_icon(self):
        response = self.client.get(reverse('users:login'))
        self.assertContains(response, 'Sign in')
        self.assertContains(response, 'profile-icon')
        self.assertContains(response, 'not your Gmail password')
        self.assertContains(response, 'Create a profile')

    def test_register_asks_only_for_email_and_password(self):
        response = self.client.get(reverse('users:register'))
        self.assertContains(response, 'Create a profile')
        self.assertContains(response, 'Your email address')
        self.assertContains(response, 'Password for this account')
        self.assertContains(response, 'not your Gmail password')
        self.assertContains(response, 'Repeat that password')


class DashboardLibraryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('buyer', 'buyer@example.com', 'pass12345')
        UserProfile.objects.get_or_create(user=self.user)

    def test_empty_library_before_purchase(self):
        Course.objects.create(title='Other course', price=Decimal('40'))
        self.client.force_login(self.user)
        response = self.client.get(reverse('users:dashboard'))
        self.assertContains(response, "You haven't bought a course yet")
        self.assertNotContains(response, 'Other course')

    def test_bought_packet_shows_watch_card(self):
        course = Course.objects.create(title='Physio', sell_as_packets=True, price=0)
        packet = Packet.objects.create(course=course, title='Cervical packet', price=Decimal('23'))
        package = packet.catalog_package
        UserAccessEntitlement.objects.create(
            user=self.user,
            product=package.product,
            package=package,
            scope=EntitlementScope.PACKAGE,
            started_at=timezone.now(),
            is_active=True,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('users:dashboard'))
        self.assertContains(response, 'Cervical packet')
        self.assertContains(response, 'Watch')
        self.assertContains(response, reverse('packet_detail', args=[course.id, packet.id]))


class TrafficExportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('staff', 'staff@example.com', 'secret')
        from datetime import date
        from users.models import SiteDailyStat
        SiteDailyStat.objects.create(
            day=date(2026, 8, 29),
            page_views=12,
            unique_visitors=5,
            buy_clicks=3,
            purchases=1,
        )

    def test_guest_cannot_download(self):
        excel = self.client.get(reverse('admin:users_sitedailystat_export_excel'))
        pdf = self.client.get(reverse('admin:users_sitedailystat_export_pdf'))
        self.assertEqual(excel.status_code, 302)
        self.assertEqual(pdf.status_code, 302)

    def test_staff_gets_excel_and_pdf(self):
        self.client.force_login(self.admin)
        excel = self.client.get(reverse('admin:users_sitedailystat_export_excel'))
        pdf = self.client.get(reverse('admin:users_sitedailystat_export_pdf'))
        self.assertEqual(excel.status_code, 200)
        self.assertTrue(excel.content.startswith(b'PK'))
        self.assertIn('.xlsx', excel['Content-Disposition'])
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        self.assertIn('.pdf', pdf['Content-Disposition'])
        self.assertIn(b'Tio Academy website insights', pdf.content)
        self.assertIn(b'startxref', pdf.content)
        self.assertIn(b'2026-08-29', pdf.content)

    def test_calendar_and_day_page(self):
        self.client.force_login(self.admin)
        listing = self.client.get(reverse('admin:users_sitedailystat_changelist'))
        self.assertContains(listing, 'Click a date')
        self.assertContains(listing, 'Top list')
        self.assertContains(listing, 'Countries')
        self.assertContains(listing, 'Devices')
        self.assertContains(listing, reverse('admin:users_sitedailystat_day', args=['2026-08-29']))
        day = self.client.get(reverse('admin:users_sitedailystat_day', args=['2026-08-29']))
        self.assertContains(day, 'Insights for')
        self.assertContains(day, 'Devices')
        self.assertContains(day, 'What they paid')
        pdf = self.client.get(reverse('admin:users_sitedailystat_export_pdf') + '?day=2026-08-29')
        self.assertEqual(pdf.status_code, 200)
        self.assertIn(b'2026-08-29', pdf.content)


class VisitInsightTests(TestCase):
    def test_visit_stores_device_and_page(self):
        from users.models import SiteInsightCount
        from users.stats import record_visit
        from django.test import RequestFactory
        request = RequestFactory().get('/stats/hit/', {'p': '/courses/'})
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'
        request.META['REMOTE_ADDR'] = '10.0.0.8'
        record_visit(request)
        self.assertTrue(SiteInsightCount.objects.filter(kind='device', label='phone').exists())
        self.assertTrue(SiteInsightCount.objects.filter(kind='page', label='Courses').exists())

    def test_backfill_from_nginx_line(self):
        import tempfile
        from pathlib import Path
        from django.core.management import call_command
        from users.geo import set_data_dir
        from users.models import SiteInsightCount
        line = (
            '1.1.1.1 - - [29/Aug/2026:10:00:00 +0000] '
            '"GET /stats/hit/?p=/courses/ HTTP/1.1" 200 43 "-" '
            '"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"\n'
        )
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, 'access.log').write_text(line, encoding='utf-8')
            geo_dir = Path(folder) / 'geo'
            geo_dir.mkdir()
            (geo_dir / 'ip-country-ipv4.csv').write_text('1.1.1.1,1.1.1.1,AU\n', encoding='utf-8')
            set_data_dir(geo_dir)
            call_command('backfill_insights', log_dir=folder, skip_geo=True)
        self.assertTrue(
            SiteInsightCount.objects.filter(kind='device', label='phone', count=1).exists()
        )
        self.assertTrue(
            SiteInsightCount.objects.filter(kind='page', label='Courses', count=1).exists()
        )
        self.assertTrue(
            SiteInsightCount.objects.filter(kind='country', label='Australia', count=1).exists()
        )

    def test_country_from_ip(self):
        import tempfile
        from pathlib import Path
        from users.geo import country_from_ip, set_data_dir
        with tempfile.TemporaryDirectory() as folder:
            geo_dir = Path(folder)
            (geo_dir / 'ip-country-ipv4.csv').write_text(
                '8.8.8.8,8.8.8.8,US\n93.158.96.196,93.158.96.196,FI\n',
                encoding='utf-8',
            )
            set_data_dir(geo_dir)
            self.assertEqual(country_from_ip('8.8.8.8'), 'United States')
            self.assertEqual(country_from_ip('93.158.96.196'), 'Finland')
            self.assertEqual(country_from_ip('10.0.0.8'), '')
