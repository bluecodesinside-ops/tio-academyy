# Drop obsolete tables whose NO ACTION FKs blocked Course deletes.

from django.db import migrations


TABLES = (
    "courses_courseenrollment",
    "courses_coursevideo",
    "courses_watchprogress",
)


def drop_legacy_tables(apps, schema_editor):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s",
                [table],
            )
            if cursor.fetchone():
                cursor.execute(f"DROP TABLE {table}")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0016_restore_course_slug_state"),
    ]

    operations = [
        migrations.RunPython(drop_legacy_tables, noop_reverse),
    ]
