from catalog.models import CourseProduct, Package, PricingTier, ProductKind, months_to_days


DANCE_TIERS = (
    ('1 Video', 1, '17.00', 1, 0),
    ('3 Videos', 3, '39.00', 2, 1),
    ('6 Videos', 6, '64.00', 4, 2),
)

PHYSIO_CHAPTER_PRICE = '19.00'
PHYSIO_BUNDLE_PRICE = '199.00'


def seed_catalog(stdout=None):
    """Create the dance + physio catalog if missing. Idempotent."""
    def log(msg):
        if stdout:
            stdout.write(msg)

    dance, dance_created = CourseProduct.objects.get_or_create(
        slug='traditional-dance-videos',
        defaults={
            'kind': ProductKind.DANCE_VIDEOS,
            'title': 'Traditional Dance Videos',
            'description': 'Buy 1, 3, or 6 traditional dance videos with time-limited access.',
            'currency': 'EUR',
            'is_active': True,
        },
    )
    if dance_created:
        log('Created Traditional Dance Videos product.')
    for name, count, price, months, order in DANCE_TIERS:
        PricingTier.objects.get_or_create(
            product=dance,
            video_count=count,
            defaults={
                'name': name,
                'price': price,
                'access_duration_days': months_to_days(months),
                'discount_percent': 0,
                'is_active': True,
                'display_order': order,
            },
        )
    log('Ensured dance pricing tiers (1/3/6).')

    physio, physio_created = CourseProduct.objects.get_or_create(
        slug='physiotherapy-packages',
        defaults={
            'kind': ProductKind.PHYSIO_PACKAGES,
            'title': 'Physiotherapy Course',
            'description': '15 chapters that can be purchased individually or as a full bundle.',
            'currency': 'EUR',
            'is_active': True,
            'bundle_enabled': False,
            'bundle_title': 'All 15 Packages',
            'bundle_price': PHYSIO_BUNDLE_PRICE,
            'bundle_access_duration_days': 365,
            'expected_package_count': 15,
        },
    )
    if physio_created:
        log('Created Physiotherapy Course product.')
    else:
        physio.bundle_enabled = False
        physio.save(update_fields=['bundle_enabled', 'updated_at'])

    for number in range(1, 16):
        Package.objects.get_or_create(
            product=physio,
            chapter_number=number,
            defaults={
                'title': f'Package {number}',
                'slug': f'package-{number}',
                'description': f'Physiotherapy package {number} of 15.',
                'individual_price': PHYSIO_CHAPTER_PRICE,
                'access_duration_days': 90,
                'is_active': True,
                'display_order': number,
            },
        )
    log('Ensured 15 physiotherapy chapters.')
    return dance, physio
