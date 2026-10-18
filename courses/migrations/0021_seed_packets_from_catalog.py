from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Packet = apps.get_model('courses', 'Packet')
    CourseProduct = apps.get_model('catalog', 'CourseProduct')
    Package = apps.get_model('catalog', 'Package')

    for product in CourseProduct.objects.filter(kind='physio_packages', linked_course_id__isnull=False):
        course = Course.objects.filter(pk=product.linked_course_id).first()
        if course is None:
            continue
        course.sell_as_packets = True
        course.save(update_fields=['sell_as_packets'])
        used_slugs = set()
        for package in Package.objects.filter(product_id=product.id).order_by('display_order', 'chapter_number', 'id'):
            if package.course_packet_id:
                continue
            order = package.chapter_number or package.display_order or 1
            base = slugify(package.title) or f'packet-{order}'
            slug = base[:80]
            n = 2
            while slug in used_slugs or Packet.objects.filter(course_id=course.id, slug=slug).exists():
                slug = f'{base[:70]}-{n}'
                n += 1
            used_slugs.add(slug)
            packet = Packet.objects.create(
                course_id=course.id,
                title=package.title,
                slug=slug,
                description=package.description or '',
                price=package.individual_price or 19,
                order=order,
                access_duration_days=package.access_duration_days or 90,
                is_active=package.is_active,
                cover=package.cover,
            )
            package.course_packet_id = packet.id
            package.save(update_fields=['course_packet_id'])


def backwards(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Course.objects.filter(sell_as_packets=True).update(sell_as_packets=False)


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0020_packet_structure'),
        ('catalog', '0006_packet_structure'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
