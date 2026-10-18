from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class ProductKind(models.TextChoices):
    DANCE_VIDEOS = 'dance_videos', 'Traditional Dance Videos'
    PHYSIO_PACKAGES = 'physio_packages', 'Physiotherapy Packages'


class EntitlementScope(models.TextChoices):
    SELECTED_ASSETS = 'selected_assets', 'Selected dance videos'
    PACKAGE = 'package', 'Single physiotherapy chapter'
    PACKAGES = 'packages', 'Selected physiotherapy chapters'
    FULL_BUNDLE = 'full_bundle', 'All packages bundle'


def months_to_days(months):
    """Canonical duration: 1 month = 30 days."""
    return int(months or 0) * 30


ACCESS_LENGTH_CHOICES = (
    (30, '1 month'),
    (90, '3 months'),
    (180, '6 months'),
    (0, 'Lifetime'),
)


class CourseProduct(models.Model):
    """Top-level sellable catalog item (dance video store or physio course)."""

    kind = models.CharField(max_length=32, choices=ProductKind.choices)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    currency = models.CharField(max_length=3, default='EUR')
    linked_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='catalog_products',
        help_text='Optional existing Course whose videos can be mapped as MediaAssets.',
    )
    bundle_enabled = models.BooleanField(
        default=False,
        help_text='Physio: allow purchasing all chapters at a bundle rate.',
    )
    bundle_title = models.CharField(max_length=200, blank=True, default='All 15 Packages')
    bundle_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    bundle_access_duration_days = models.PositiveIntegerField(
        default=365,
        help_text='0 = lifetime. Access length when the full physio bundle is purchased.',
    )
    expected_package_count = models.PositiveSmallIntegerField(
        default=15,
        help_text='Physio: expected number of chapters (default 15).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['kind', 'title']
        verbose_name = 'Dance / Physio product'
        verbose_name_plural = 'Dance & Physio products'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title) or 'product'
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.kind == ProductKind.PHYSIO_PACKAGES and self.bundle_enabled and self.bundle_price <= 0:
            raise ValidationError({'bundle_price': 'Bundle price must be greater than 0 when the bundle is enabled.'})

    @property
    def bundle_access_duration_months(self):
        return (self.bundle_access_duration_days or 0) // 30

    def active_tiers(self):
        return self.pricing_tiers.filter(is_active=True).order_by('display_order', 'video_count')

    def active_packages(self):
        return self.packages.filter(is_active=True).order_by('display_order', 'chapter_number', 'id')


class PricingTier(models.Model):
    """Dance video bundle: N videos for a price and a time-limited entitlement."""

    product = models.ForeignKey(CourseProduct, on_delete=models.CASCADE, related_name='pricing_tiers')
    name = models.CharField(max_length=100)
    video_count = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    access_duration_days = models.PositiveIntegerField(
        help_text='Canonical duration in days (1 month = 30, 2 months = 60, 4 months = 120).',
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Optional extra discount applied at checkout on top of the listed price.',
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    stripe_price_id = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['display_order', 'video_count']
        unique_together = ['product', 'video_count']
        verbose_name = 'Dance video tier'
        verbose_name_plural = 'Dance video tiers'

    def __str__(self):
        return f'{self.product.title} — {self.name}'

    def clean(self):
        super().clean()
        if self.product_id and self.product.kind != ProductKind.DANCE_VIDEOS:
            raise ValidationError('Pricing tiers are only valid on Traditional Dance Video products.')
        if self.price <= 0:
            raise ValidationError({'price': 'Price must be greater than 0.'})
        if self.access_duration_days <= 0:
            raise ValidationError({'access_duration_days': 'Access duration must be at least 1 day.'})

    @property
    def access_duration_months(self):
        return (self.access_duration_days or 0) // 30

    def resolved_price(self):
        from catalog.services.pricing import resolve_tier_price
        return resolve_tier_price(self)


class Package(models.Model):
    """Physiotherapy chapter/package (1 of 15), or an optional dance grouping."""

    product = models.ForeignKey(CourseProduct, on_delete=models.CASCADE, related_name='packages')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    chapter_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Physio chapter number (1–15).',
    )
    individual_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    cover = models.ImageField(
        upload_to='catalog/packages/',
        blank=True,
        null=True,
        help_text='Cover image for this package on the course page.',
    )
    course_packet = models.OneToOneField(
        'courses.Packet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='catalog_package',
        help_text='Course packet this catalog row sells.',
    )
    access_duration_days = models.PositiveIntegerField(
        default=90,
        help_text='0 = lifetime. Used when this chapter is purchased on its own.',
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'chapter_number', 'id']
        unique_together = ['product', 'slug']
        verbose_name = 'Physio chapter'
        verbose_name_plural = 'Physio chapters'
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'chapter_number'],
                name='catalog_package_unique_chapter',
                condition=models.Q(chapter_number__isnull=False),
            ),
        ]

    def __str__(self):
        if self.chapter_number:
            return f'Ch. {self.chapter_number}: {self.title}'
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or f'chapter-{self.chapter_number or "package"}'
            self.slug = base[:200]
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.product_id and self.product.kind == ProductKind.PHYSIO_PACKAGES:
            if not self.chapter_number:
                raise ValidationError({'chapter_number': 'Physiotherapy packages need a chapter number.'})
            expected = self.product.expected_package_count or 15
            if self.chapter_number > expected:
                raise ValidationError({'chapter_number': f'Chapter number cannot exceed {expected}.'})
            if self.individual_price <= 0:
                raise ValidationError({'individual_price': 'Set an individual price greater than 0.'})

    def get_cover_url(self):
        if self.cover:
            return self.cover.url
        asset = (
            self.media_assets.filter(is_active=True)
            .select_related('session')
            .order_by('order', 'id')
            .first()
        )
        if asset and asset.cover:
            return asset.cover.url
        if asset and asset.session_id:
            return asset.session.get_cover_url()
        product = self.product
        if product and product.linked_course_id and product.linked_course.image:
            return product.linked_course.image.url
        return None


class MediaAsset(models.Model):
    """A video that can be sold in a dance tier or attached to a physio chapter."""

    product = models.ForeignKey(CourseProduct, on_delete=models.CASCADE, related_name='media_assets')
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name='media_assets',
        null=True,
        blank=True,
        help_text='Required for physiotherapy chapters. Optional grouping for dance videos.',
    )
    session = models.ForeignKey(
        'courses.Session',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='catalog_assets',
        help_text='Map to an existing course video so entitlements unlock playback.',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='catalog/videos/', blank=True, null=True)
    cover = models.ImageField(upload_to='catalog/covers/', blank=True, null=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    allowed_tiers = models.ManyToManyField(
        PricingTier,
        blank=True,
        related_name='mapped_assets',
        help_text='Dance: leave empty to allow this video in every active tier.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Catalog video'
        verbose_name_plural = 'Catalog videos'

    def __str__(self):
        return self.title

    def get_cover_url(self):
        if self.cover:
            return self.cover.url
        if self.session_id:
            return self.session.get_cover_url()
        return None

    def duration_minutes(self):
        if self.duration_seconds:
            return max(1, int(round(self.duration_seconds / 60)))
        if self.session_id and getattr(self.session, 'duration', None):
            return self.session.duration
        return None

    def clean(self):
        super().clean()
        if self.package_id and self.product_id and self.package.product_id != self.product_id:
            raise ValidationError({'package': 'Package must belong to the same product.'})
        if not self.session_id and not self.video_url and not self.video_file:
            raise ValidationError('Attach a course video, paste a URL, or upload a file.')

    def is_allowed_in_tier(self, tier):
        if not self.is_active:
            return False
        if self.product_id != tier.product_id:
            return False
        if not self.allowed_tiers.exists():
            return True
        return self.allowed_tiers.filter(pk=tier.pk).exists()


class UserAccessEntitlement(models.Model):
    """Time-bound access grant for selected videos, a chapter, or a full bundle."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='access_entitlements')
    product = models.ForeignKey(CourseProduct, on_delete=models.CASCADE, related_name='entitlements')
    pricing_tier = models.ForeignKey(
        PricingTier, on_delete=models.SET_NULL, null=True, blank=True, related_name='entitlements',
    )
    package = models.ForeignKey(
        Package, on_delete=models.SET_NULL, null=True, blank=True, related_name='entitlements',
    )
    scope = models.CharField(max_length=32, choices=EntitlementScope.choices)
    media_assets = models.ManyToManyField(MediaAsset, blank=True, related_name='entitlements')
    packages = models.ManyToManyField(
        Package, blank=True, related_name='multi_entitlements',
        help_text='Selected physio chapters when the buyer did not take the full bundle.',
    )
    started_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='granted_entitlements',
        help_text='Staff user if this entitlement was granted from admin.',
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Purchase'
        verbose_name_plural = 'Purchases'
        indexes = [
            models.Index(fields=['user', 'product', 'is_active']),
        ]

    def __str__(self):
        return f'{self.user} — {self.product} ({self.scope})'

    def clean(self):
        super().clean()
        if self.scope == EntitlementScope.SELECTED_ASSETS and not self.pricing_tier_id:
            raise ValidationError({'pricing_tier': 'Dance entitlements need a pricing tier.'})
        if self.scope == EntitlementScope.PACKAGE and not self.package_id:
            raise ValidationError({'package': 'Chapter entitlements need a package.'})
        if self.expires_at and self.started_at and self.expires_at <= self.started_at:
            raise ValidationError({'expires_at': 'Expiry must be after the start time.'})

    def is_currently_valid(self, at=None):
        if not self.is_active:
            return False
        now = at or timezone.now()
        if self.started_at and now < self.started_at:
            return False
        if self.expires_at and now >= self.expires_at:
            return False
        return True

    def remaining_days(self, at=None):
        if not self.is_currently_valid(at=at) or not self.expires_at:
            return 0
        now = at or timezone.now()
        return max(0, (self.expires_at - now).days)

    @staticmethod
    def compute_expiry(started_at, duration_days):
        if not duration_days:
            return None
        return started_at + timedelta(days=int(duration_days))
