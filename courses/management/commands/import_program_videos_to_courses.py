"""
Optional one-shot: copy legacy Programs videos into Course sessions.

Only creates a Course per DanceStyle that has videos and is missing a
matching Course title. Safe to re-run (skips styles already mapped).

Usage:
  python manage.py import_program_videos_to_courses --dry-run
  python manage.py import_program_videos_to_courses
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from courses.models import Course, Session
from programs.models import DanceStyle, Video


class Command(BaseCommand):
    help = 'Import Programs (DanceStyle/Video) into Courses/Sessions when useful.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be created without writing.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options['dry_run']
        created_courses = 0
        created_sessions = 0

        for style in DanceStyle.objects.filter(is_active=True).order_by('order', 'name'):
            videos = list(
                Video.objects.filter(
                    skill_level__category__dance_style=style,
                    is_active=True,
                )
                .select_related('skill_level', 'skill_level__category')
                .order_by(
                    'skill_level__category__order',
                    'skill_level__order',
                    'order',
                    'id',
                )
            )
            if not videos:
                self.stdout.write(f'Skip {style.name!r}: no videos')
                continue

            existing = Course.objects.filter(title__iexact=style.name).first()
            if existing and existing.sessions.exists():
                self.stdout.write(
                    f'Skip {style.name!r}: Course already has sessions (id={existing.id})'
                )
                continue

            if dry:
                self.stdout.write(
                    f'[dry-run] Would create/update Course {style.name!r} '
                    f'with {len(videos)} session(s)'
                )
                continue

            course = existing
            if not course:
                base_slug = slugify(style.name) or f'style-{style.id}'
                slug = base_slug
                n = 1
                while Course.objects.filter(slug=slug).exists():
                    n += 1
                    slug = f'{base_slug}-{n}'
                course = Course(
                    title=style.name,
                    slug=slug,
                    description=style.description or '',
                    is_active=True,
                    price=0,
                )
                if style.image:
                    course.image = style.image
                course.save()
                created_courses += 1
                self.stdout.write(self.style.SUCCESS(f'Created Course {course.title!r}'))

            for i, video in enumerate(videos, start=1):
                if Session.objects.filter(course=course, title=video.title).exists():
                    continue
                session = Session(
                    course=course,
                    title=video.title,
                    description=video.description or '',
                    video_url=video.video_url or '',
                    duration=max(1, int(round((video.duration or 60) / 60))) if video.duration else 5,
                    order=i,
                    is_free_preview=(i == 1 or video.is_free),
                    is_active=True,
                )
                if video.video_file:
                    session.video_file = video.video_file
                session.save()
                created_sessions += 1

        if dry:
            self.stdout.write(self.style.WARNING('Dry run complete — no changes written.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Done. Courses created: {created_courses}, sessions created: {created_sessions}'
                )
            )
