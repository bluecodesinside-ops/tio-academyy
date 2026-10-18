# Generated manually — optional cover image per course video (Session)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0018_cleanup_legacy_sitesection_tier'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='cover',
            field=models.ImageField(
                blank=True,
                help_text='Video cover / thumbnail shown in the course list and player poster. Falls back to course cover if empty.',
                null=True,
                upload_to='sessions/covers/',
            ),
        ),
    ]
