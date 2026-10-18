from django.db import migrations, models


def copy_packet_titles(apps, schema_editor):
    Packet = apps.get_model('courses', 'Packet')
    for packet in Packet.objects.all():
        title = packet.title or ''
        description = packet.description or ''
        if not packet.title_en:
            packet.title_en = title
        if not packet.title_sq:
            packet.title_sq = title
        if description and not packet.description_en:
            packet.description_en = description
        if description and not packet.description_sq:
            packet.description_sq = description
        packet.save()


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0021_seed_packets_from_catalog'),
    ]

    operations = [
        migrations.AddField(
            model_name='packet',
            name='title_en',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='packet',
            name='title_sq',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='packet',
            name='description_en',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='packet',
            name='description_sq',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(copy_packet_titles, migrations.RunPython.noop),
    ]
