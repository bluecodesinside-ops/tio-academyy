from django.db import migrations


def seed_forward(apps, schema_editor):
    # Seed uses the current Package model (including later fields like cover).
    # Creating catalog rows is handled by seed_catalog() after migrations.
    return


def seed_reverse(apps, schema_editor):
    CourseProduct = apps.get_model('catalog', 'CourseProduct')
    CourseProduct.objects.filter(slug__in=['traditional-dance-videos', 'physiotherapy-packages']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_forward, seed_reverse),
    ]
