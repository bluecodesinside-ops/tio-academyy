from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0015_backfill_session_course"),
    ]
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="course",
                    name="slug",
                    field=models.SlugField(
                        blank=True,
                        help_text="Auto-generated from title if left blank.",
                        max_length=50,
                        unique=True,
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
