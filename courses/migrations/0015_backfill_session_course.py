# Generated manually — backfill Session.course and free-preview flags

from django.db import migrations


def flatten_sessions(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Session = apps.get_model('courses', 'Session')
    Level = apps.get_model('courses', 'Level')

    for course in Course.objects.all():
        # Collect sessions via level (legacy) or already-linked course
        via_level = list(
            Session.objects.filter(level__course=course).order_by('level__order', 'order', 'id')
        )
        via_course = list(
            Session.objects.filter(course=course).order_by('order', 'id')
        )
        # Preserve order; prefer level ordering when present
        seen = set()
        ordered = []
        for s in via_level + via_course:
            if s.id in seen:
                continue
            seen.add(s.id)
            ordered.append(s)

        if not ordered and not course.levels.exists():
            Level.objects.create(course=course, name='Videos', description='', order=1)

        default_level = course.levels.order_by('order').first()
        if not default_level:
            default_level = Level.objects.create(
                course=course, name='Videos', description='', order=1
            )

        # Temporary high orders to avoid unique conflicts while renumbering
        for i, session in enumerate(ordered):
            session.course_id = course.id
            if not session.level_id:
                session.level_id = default_level.id
            session.order = 10000 + i
            session.is_free_preview = False
            session.save(update_fields=['course', 'level', 'order', 'is_free_preview'])

        for i, session in enumerate(ordered, start=1):
            session.order = i
            session.is_free_preview = i == 1
            session.save(update_fields=['order', 'is_free_preview'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0014_course_sessions_flatten'),
    ]

    operations = [
        migrations.RunPython(flatten_sessions, noop_reverse),
    ]
