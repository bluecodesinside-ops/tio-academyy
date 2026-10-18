from django.db import connection, models, transaction
from django.contrib.auth.models import User
from django.utils.text import slugify


# Leftover SQLite tables from older schemas. Django no longer models them, but
# their NO ACTION FKs still block Course/Session deletes.
_LEGACY_COURSE_FK_TABLES = (
    'courses_courseenrollment',
    'courses_coursevideo',
)
_LEGACY_SESSION_FK_TABLES = (
    'courses_watchprogress',
)


def _table_exists(cursor, name):
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=%s",
        [name],
    )
    return cursor.fetchone() is not None


def purge_legacy_course_fk_rows(course_ids):
    """Remove rows in obsolete tables that FK to the given course ids."""
    ids = [int(i) for i in course_ids if i is not None]
    if not ids:
        return
    placeholders = ','.join(['%s'] * len(ids))
    with connection.cursor() as cursor:
        for table in _LEGACY_COURSE_FK_TABLES:
            if _table_exists(cursor, table):
                cursor.execute(
                    f'DELETE FROM {table} WHERE course_id IN ({placeholders})',
                    ids,
                )

        session_ids = []
        if _table_exists(cursor, 'courses_session'):
            cursor.execute(
                f'''
                SELECT s.id FROM courses_session s
                LEFT JOIN courses_level l ON s.level_id = l.id
                WHERE s.course_id IN ({placeholders})
                   OR l.course_id IN ({placeholders})
                ''',
                ids + ids,
            )
            session_ids = [row[0] for row in cursor.fetchall()]

        if session_ids:
            sess_ph = ','.join(['%s'] * len(session_ids))
            for table in _LEGACY_SESSION_FK_TABLES:
                if _table_exists(cursor, table):
                    cursor.execute(
                        f'DELETE FROM {table} WHERE session_id IN ({sess_ph})',
                        session_ids,
                    )


class CourseQuerySet(models.QuerySet):
    def delete(self):
        ids = list(self.values_list('pk', flat=True))
        if not ids:
            return (0, {})
        with transaction.atomic():
            purge_legacy_course_fk_rows(ids)
            return super().delete()


class Course(models.Model):
    """A sellable course: cover + title + ordered videos (sessions)."""
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        help_text='Auto-generated from title if left blank.',
    )
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='courses/',
        blank=True,
        null=True,
        help_text='Cover image shown on course cards',
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration = models.CharField(max_length=50, blank=True, help_text="e.g., '12 videos'")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Used when this course is sold as one unlock. Ignored when Sell as packets is on.',
    )
    sell_as_packets = models.BooleanField(
        default=False,
        help_text='Udemy-style: course is a container of packets. Each packet has its own cover, price, and videos.',
    )
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CourseQuerySet.as_manager()

    class Meta:
        ordering = ['title']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return self.title or f'Course #{self.pk}'

    def _unique_slug(self, base):
        """Return a unique slug ≤ 50 chars derived from base."""
        base = (base or 'course')[:50].strip('-') or 'course'
        candidate = base
        n = 2
        qs = Course.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.filter(slug=candidate).exists():
            suffix = f'-{n}'
            candidate = f'{base[:50 - len(suffix)]}{suffix}'
            n += 1
        return candidate

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'course'
            self.slug = self._unique_slug(base)
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        with transaction.atomic(using=using):
            if self.pk:
                purge_legacy_course_fk_rows([self.pk])
            return super().delete(using=using, keep_parents=keep_parents)

    def get_ordered_sessions(self, active_only=True):
        """Flat ordered video list for this course (preferred over Level nesting)."""
        qs = self.sessions.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return qs.order_by('packet__order', 'packet_id', 'order', 'id')

    def get_preview_sessions(self):
        """Every video marked free preview, packet order first."""
        return list(
            self.sessions.filter(is_active=True, is_free_preview=True).order_by(
                'packet__order', 'packet_id', 'order', 'id'
            )
        )

    def get_preview_session(self):
        """Video marked as free preview, if any. First in the list is not automatic."""
        previews = self.get_preview_sessions()
        return previews[0] if previews else None

    def get_total_sessions(self):
        count = self.sessions.filter(is_active=True).count()
        if count:
            return count
        return sum(level.sessions.filter(is_active=True).count() for level in self.levels.all())

    def get_total_duration(self):
        sessions = list(self.get_ordered_sessions())
        if not sessions:
            sessions = [
                s
                for level in self.levels.all()
                for s in level.sessions.filter(is_active=True)
            ]
        total_minutes = sum(s.duration or 0 for s in sessions)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours > 0:
            return f'{hours}h {minutes}m'
        return f'{minutes}m'

    def ensure_default_level(self):
        """Keep one backing Level for legacy code paths."""
        level = self.levels.order_by('order').first()
        if level:
            return level
        return Level.objects.create(
            course=self,
            name='Videos',
            description='',
            order=1,
        )


class Level(models.Model):
    """Optional grouping under a course (legacy). Prefer flat Course → Session."""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='levels')
    name = models.CharField(max_length=50, default='Videos')
    description = models.TextField(blank=True)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']
        verbose_name = 'Level (optional)'
        verbose_name_plural = 'Levels (optional — prefer Videos on Course)'

    def __str__(self):
        return f'{self.course.title} - {self.name}'


class Session(models.Model):
    """A single video lesson under a course (Bunny / YouTube / file)."""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions',
        null=True,
        blank=True,
        help_text='Primary parent. Prefer this over Level.',
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='sessions',
        null=True,
        blank=True,
        help_text='Optional legacy grouping. Auto-filled if empty.',
    )
    packet = models.ForeignKey(
        'Packet',
        on_delete=models.SET_NULL,
        related_name='videos',
        null=True,
        blank=True,
        help_text='Packet / module this video belongs to.',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cover = models.ImageField(
        upload_to='sessions/covers/',
        blank=True,
        null=True,
        help_text='Video cover / thumbnail shown in the course list and player poster. Falls back to course cover if empty.',
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        help_text='Bunny.net embed/play URL, YouTube, or direct MP4 URL',
    )
    video_file = models.FileField(
        upload_to='videos/sessions/',
        blank=True,
        null=True,
        help_text='Optional local upload (prefer Bunny URL for production)',
    )
    duration = models.IntegerField(help_text='Duration in minutes', default=20)
    order = models.IntegerField(default=1, help_text='Display order. 1 is first in the list, not automatically free.')
    is_free_preview = models.BooleanField(
        default=False,
        help_text='Tick this box to make THIS video the free preview. Leave empty to keep it locked.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'

    def __str__(self):
        course_title = ''
        if self.course_id:
            course_title = self.course.title
        elif self.level_id:
            course_title = self.level.course.title
        return f'{course_title} — {self.title}' if course_title else self.title

    def save(self, *args, **kwargs):
        if self.packet_id:
            if self.packet.course_id:
                self.course = self.packet.course
        if self.level_id and not self.course_id:
            self.course = self.level.course
        if self.course_id and not self.level_id:
            self.level = self.course.ensure_default_level()

        creating = self.pk is None
        super().save(*args, **kwargs)

        if self.course_id:
            self._ensure_preview_flags(prefer_self=creating or self.is_free_preview)

    def _ensure_preview_flags(self, prefer_self=False):
        """At most one free preview per packet (or per course if not in a packet)."""
        if not self.is_free_preview:
            return
        qs = Session.objects.filter(is_free_preview=True).exclude(pk=self.pk)
        if self.packet_id:
            qs = qs.filter(packet_id=self.packet_id)
        else:
            qs = qs.filter(course_id=self.course_id)
        qs.update(is_free_preview=False)

    def get_youtube_id(self):
        if not self.is_youtube_url():
            return None
        url = self.video_url or ''
        if 'youtube.com/watch?v=' in url:
            return url.split('v=')[1].split('&')[0]
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[1].split('?')[0]
        if 'youtube.com/embed/' in url:
            return url.split('embed/')[1].split('?')[0]
        return None

    def get_cover_url(self):
        """Video cover, YouTube thumb, course cover, or None."""
        if self.cover:
            return self.cover.url
        youtube_id = self.get_youtube_id()
        if youtube_id:
            return f'https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg'
        course = self.course
        if not course and self.level_id:
            course = self.level.course
        if course and course.image:
            return course.image.url
        return None

    def get_video_source(self):
        if self.video_file:
            return 'file'
        if self.video_url:
            return 'url'
        return None

    def is_youtube_url(self):
        if not self.video_url:
            return False
        url = self.video_url.lower()
        return 'youtube.com' in url or 'youtu.be' in url

    def is_bunny_embed_url(self):
        """Bunny Stream iframe / mediadelivery embed."""
        if not self.video_url:
            return False
        url = self.video_url.lower()
        return (
            'mediadelivery.net' in url
            or 'iframe.mediadelivery.net' in url
            or 'bunny.net/embed' in url
        )

    def is_direct_video_url(self):
        """CDN / Bunny pull zone / MP4-style URL for HTML5 <video>."""
        if not self.video_url or self.is_youtube_url() or self.is_bunny_embed_url():
            return False
        url = self.video_url.lower()
        if any(ext in url.split('?')[0] for ext in ('.mp4', '.webm', '.m3u8', '.mov')):
            return True
        if 'b-cdn.net' in url or 'bunnycdn' in url or 'vz-' in url:
            return True
        return True  # treat other external URLs as playable/direct by default

    def get_youtube_embed_url(self):
        if not self.is_youtube_url():
            return None
        if 'youtube.com/watch?v=' in self.video_url:
            video_id = self.video_url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in self.video_url:
            video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
        elif 'youtube.com/embed/' in self.video_url:
            video_id = self.video_url.split('embed/')[1].split('?')[0]
        else:
            return None
        return f'https://www.youtube.com/embed/{video_id}?playsinline=1&rel=0'

    def get_bunny_ids(self):
        if not self.video_url or not self.is_bunny_embed_url():
            return None
        import re
        match = re.search(
            r'(?:player|iframe)\.mediadelivery\.net/(?:play|embed)/([^/\s?#]+)/([^/\s?#]+)',
            self.video_url,
            re.IGNORECASE,
        )
        if not match:
            return None
        return match.group(1), match.group(2)

    def get_bunny_play_url(self):
        """Top-level Bunny player page — this is what actually works on iPhones."""
        ids = self.get_bunny_ids()
        if not ids:
            return None
        library_id, video_id = ids
        return f'https://player.mediadelivery.net/play/{library_id}/{video_id}'

    def get_bunny_embed_url(self):
        """Normalize Bunny play/share URLs to iframe embed URLs."""
        ids = self.get_bunny_ids()
        if ids:
            library_id, video_id = ids
            return (
                f'https://iframe.mediadelivery.net/embed/{library_id}/{video_id}'
                f'?autoplay=false&preload=true&playsinline=true'
            )
        if not self.video_url or not self.is_bunny_embed_url():
            return None
        url = self.video_url
        if 'playsinline' not in url.lower():
            joiner = '&' if '?' in url else '?'
            return f'{url}{joiner}autoplay=false&playsinline=true'
        return url

    def get_embed_url(self):
        """Best iframe src for YouTube or Bunny Stream embeds."""
        if self.is_youtube_url():
            return self.get_youtube_embed_url()
        if self.is_bunny_embed_url():
            return self.get_bunny_embed_url()
        return None

    def get_playback_kind(self):
        """file | youtube | bunny_embed | direct | none"""
        if self.video_file:
            return 'file'
        if self.is_youtube_url():
            return 'youtube'
        if self.is_bunny_embed_url():
            return 'bunny_embed'
        if self.video_url:
            return 'direct'
        return 'none'


class Packet(models.Model):
    """A buyable module inside a course: own cover, own price, its own videos."""

    MAX_VIDEOS = 20

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='packets')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    cover = models.ImageField(
        upload_to='packets/covers/',
        blank=True,
        null=True,
        help_text='Cover students see when choosing this packet.',
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=19)
    order = models.PositiveIntegerField(default=1, help_text='Display order inside the course.')
    access_duration_days = models.PositiveIntegerField(
        default=90,
        help_text='0 = lifetime access after purchase.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        unique_together = ['course', 'slug']
        verbose_name = 'Packet'
        verbose_name_plural = 'Packets'

    def __str__(self):
        return f'{self.course.title} — {self.title}' if self.course_id else self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or f'packet-{self.order}'
            self.slug = base[:80]
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if self.price is not None and self.price <= 0:
            raise ValidationError({'price': 'Each packet needs a price greater than 0.'})
        if self.pk:
            count = self.videos.filter(is_active=True).count()
            if count > self.MAX_VIDEOS:
                raise ValidationError(f'A packet can have at most {self.MAX_VIDEOS} videos.')

    @property
    def individual_price(self):
        return self.price

    def video_count(self):
        return self.videos.filter(is_active=True).count()

    def get_cover_url(self):
        if self.cover:
            return self.cover.url
        video = self.videos.filter(is_active=True).order_by('order', 'id').first()
        if video:
            return video.get_cover_url()
        if self.course_id and self.course.image:
            return self.course.image.url
        return None


class UserProgress(models.Model):
    """Track user progress through course videos."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    progress_percentage = models.IntegerField(default=0, help_text='Progress percentage (0-100)')
    last_watched_position = models.IntegerField(default=0, help_text='Last watched position in seconds')
    last_watched_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'session']

    def __str__(self):
        return f'{self.user.username} - {self.session.title}'

    def is_level_completed(self):
        if not self.session.level_id:
            return False
        level_sessions = self.session.level.sessions.all()
        completed_sessions = UserProgress.objects.filter(
            user=self.user,
            session__in=level_sessions,
            completed=True,
        ).count()
        return completed_sessions == level_sessions.count()

    def get_next_session(self):
        current = self.session
        course = current.course or (current.level.course if current.level_id else None)
        if not course:
            return None
        return (
            Session.objects.filter(course=course, is_active=True, order__gt=current.order)
            .order_by('order', 'id')
            .first()
        )
