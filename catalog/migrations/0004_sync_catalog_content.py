from django.db import migrations


def forwards(apps, schema_editor):
    from catalog.services.sync import sync_catalog_content
    sync_catalog_content()


def backwards(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0003_entitlement_packages'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
