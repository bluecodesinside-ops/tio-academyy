# Production-safe: course_id and cleared unique_together already exist on live DB

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0013_add_level_required_tier"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="course",
            options={
                "ordering": ["title"],
                "verbose_name": "Course",
                "verbose_name_plural": "Courses",
            },
        ),
        migrations.AlterModelOptions(
            name="level",
            options={
                "ordering": ["order"],
                "verbose_name": "Level (optional)",
                "verbose_name_plural": "Levels (optional — prefer Videos on Course)",
            },
        ),
        migrations.AlterModelOptions(
            name="session",
            options={
                "ordering": ["order", "id"],
                "verbose_name": "Video",
                "verbose_name_plural": "Videos",
            },
        ),
        # Live DB already has no (level, order) unique constraint and already has course_id.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterUniqueTogether(
                    name="session",
                    unique_together=set(),
                ),
                migrations.AddField(
                    model_name="session",
                    name="course",
                    field=models.ForeignKey(
                        blank=True,
                        help_text="Primary parent. Prefer this over Level.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="courses.course",
                    ),
                ),
            ],
            database_operations=[],
        ),
        migrations.AddField(
            model_name="session",
            name="is_free_preview",
            field=models.BooleanField(
                default=False,
                help_text="Free preview without purchase. First video is auto-marked if none set.",
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="course",
            name="description_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="course",
            name="description_sq",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="course",
            name="duration",
            field=models.CharField(
                blank=True, help_text="e.g., '12 videos'", max_length=50
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="Cover image shown on course cards",
                null=True,
                upload_to="courses/",
            ),
        ),
        migrations.AlterField(
            model_name="course",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text="Full course price. First video stays free as preview.",
                max_digits=10,
            ),
        ),
        migrations.AlterField(
            model_name="level",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="level",
            name="description_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="level",
            name="description_sq",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="level",
            name="name",
            field=models.CharField(default="Videos", max_length=50),
        ),
        migrations.AlterField(
            model_name="level",
            name="name_en",
            field=models.CharField(default="Videos", max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="level",
            name="name_sq",
            field=models.CharField(default="Videos", max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="session",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="session",
            name="description_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="session",
            name="description_sq",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="session",
            name="level",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional legacy grouping. Auto-filled if empty.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sessions",
                to="courses.level",
            ),
        ),
        migrations.AlterField(
            model_name="session",
            name="order",
            field=models.IntegerField(
                default=1, help_text="1 = first (free preview by default)"
            ),
        ),
        migrations.AlterField(
            model_name="session",
            name="video_file",
            field=models.FileField(
                blank=True,
                help_text="Optional local upload (prefer Bunny URL for production)",
                null=True,
                upload_to="videos/sessions/",
            ),
        ),
        migrations.AlterField(
            model_name="session",
            name="video_url",
            field=models.URLField(
                blank=True,
                help_text="Bunny.net embed/play URL, YouTube, or direct MP4 URL",
                null=True,
            ),
        ),
    ]
