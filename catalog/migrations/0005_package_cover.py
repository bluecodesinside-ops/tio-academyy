from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0004_sync_catalog_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='cover',
            field=models.ImageField(
                blank=True,
                help_text='Cover image for this package on the course page.',
                null=True,
                upload_to='catalog/packages/',
            ),
        ),
    ]
