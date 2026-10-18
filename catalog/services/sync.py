"""Link catalog products to live courses. Physio videos stay unassigned until admin places them."""
from catalog.models import CourseProduct, MediaAsset, ProductKind
from courses.models import Course


DANCE_SLUGS = ('traditional-dancing',)
PHYSIO_SLUGS = ('fizioterapi',)
DANCE_TITLE_MARKERS = ('vallet', 'vallje', 'traditional')
PHYSIO_TITLE_MARKERS = ('levizje', 'fizioterapi', 'physio', 'mireqenie')


def _course_by_slug_or_title(slugs, markers):
    from django.db.utils import OperationalError
    try:
        for slug in slugs:
            course = Course.objects.filter(slug=slug, is_active=True).first()
            if course:
                return course
    except OperationalError:
        pass
    for marker in markers:
        course = Course.objects.filter(title__icontains=marker, is_active=True).first()
        if course:
            return course
    return None


def _ordered_sessions(course):
    return list(course.get_ordered_sessions())


def _upsert_asset(product, session, package=None, order=0):
    asset, created = MediaAsset.objects.get_or_create(
        product=product,
        session=session,
        defaults={
            'package': package,
            'title': session.title,
            'description': session.description or '',
            'video_url': session.video_url or '',
            'duration_seconds': (session.duration or 0) * 60,
            'order': order or session.order or 0,
            'is_active': session.is_active,
        },
    )
    fields = []
    if package and asset.package_id != package.id:
        asset.package = package
        fields.append('package')
    if asset.title != session.title:
        asset.title = session.title
        fields.append('title')
    if session.video_url and asset.video_url != session.video_url:
        asset.video_url = session.video_url
        fields.append('video_url')
    if fields:
        asset.save(update_fields=fields + ['updated_at'])
    return asset, created


def sync_catalog_content(stdout=None):
    """Attach the seeded dance/physio products to the live courses and map videos."""
    from django.db.utils import OperationalError

    def log(msg):
        if stdout:
            stdout.write(msg)

    try:
        return _sync_catalog_content(log)
    except OperationalError as exc:
        log(f'Skipped catalog content sync: {exc}')
        return None, None


def _sync_catalog_content(log):
    dance = CourseProduct.objects.filter(kind=ProductKind.DANCE_VIDEOS).first()
    physio = CourseProduct.objects.filter(kind=ProductKind.PHYSIO_PACKAGES).first()

    dance_course = _course_by_slug_or_title(DANCE_SLUGS, DANCE_TITLE_MARKERS)
    if dance and dance_course:
        dance.linked_course = dance_course
        dance.save(update_fields=['linked_course', 'updated_at'])
        for session in _ordered_sessions(dance_course):
            _upsert_asset(dance, session, order=session.order)
        log(f'Linked dance catalog to {dance_course.title} ({dance.media_assets.count()} videos).')

    physio_course = _course_by_slug_or_title(PHYSIO_SLUGS, PHYSIO_TITLE_MARKERS)
    if physio and physio_course:
        physio.linked_course = physio_course
        physio.bundle_enabled = False
        physio.save(update_fields=['linked_course', 'bundle_enabled', 'updated_at'])
        for session in _ordered_sessions(physio_course):
            _upsert_asset(physio, session, package=None, order=session.order)
        log(
            f'Linked physio catalog to {physio_course.title} '
            f'({physio.packages.filter(is_active=True).count()} packages, '
            f'{physio.media_assets.count()} videos ready to assign).'
        )

    return dance, physio


def reset_physio_assignments_for_manual_setup(stdout=None):
    """Empty the 15 packages so staff can place videos and set each package price."""
    def log(msg):
        if stdout:
            stdout.write(msg)

    physio = CourseProduct.objects.filter(kind=ProductKind.PHYSIO_PACKAGES).first()
    if not physio:
        log('No physiotherapy product found.')
        return None
    cleared = physio.media_assets.update(package=None)
    physio.bundle_enabled = False
    physio.save(update_fields=['bundle_enabled', 'updated_at'])
    for package in physio.packages.all():
        number = package.chapter_number or package.display_order or package.id
        package.title = f'Package {number}'
        package.description = f'Physiotherapy package {number} of 15.'
        package.save(update_fields=['title', 'description', 'updated_at'])
    log(f'Reset {physio.packages.count()} packages and unassigned {cleared} videos.')
    return physio


def restore_physio_course_from_catalog(stdout=None):
    """Rebuild the physio course as a video library. Selling stays on the 15 packages."""
    from decimal import Decimal
    from courses.models import Course, Session

    def log(msg):
        if stdout:
            stdout.write(msg)

    physio = CourseProduct.objects.filter(kind=ProductKind.PHYSIO_PACKAGES).first()
    if not physio:
        log('No physiotherapy product found.')
        return None
    assets = list(physio.media_assets.filter(is_active=True).order_by('id'))
    if not assets:
        log('No physiotherapy videos left in the catalog to restore.')
        return None

    course = physio.linked_course
    if course is None:
        course = Course.objects.filter(slug='fizioterapi').first()
    if course is None:
        course = Course.objects.create(
            title='PROGRAME PER LEVIZJE DHE MIREQENIE',
            slug='fizioterapi',
            description='Buy the packages you want. Each package has its own price.',
            price=Decimal('19.00'),
            duration='15 packages',
            level='beginner',
            is_active=True,
        )
        log(f'Created physiotherapy course #{course.id}.')
    else:
        course.is_active = True
        if course.price <= 0:
            course.price = Decimal('19.00')
        course.save(update_fields=['is_active', 'price', 'updated_at'])

    physio.linked_course = course
    physio.bundle_enabled = False
    physio.save(update_fields=['linked_course', 'bundle_enabled', 'updated_at'])

    created = 0
    for index, asset in enumerate(assets, start=1):
        session = asset.session
        if session is None or session.course_id != course.id:
            session = Session(
                course=course,
                title=(asset.title or f'Video {index}')[:200],
                description=asset.description or '',
                video_url=asset.video_url or '',
                duration=max(1, (asset.duration_seconds or 0) // 60) or 20,
                order=index,
                is_free_preview=False,
                is_active=True,
            )
            session.save()
            created += 1
        else:
            session.course = course
            session.title = (asset.title or session.title)[:200]
            session.video_url = asset.video_url or session.video_url
            session.order = index
            session.is_active = True
            session.save()
        if asset.session_id != session.id or asset.order != index:
            asset.session = session
            asset.order = index
            asset.save(update_fields=['session', 'order', 'updated_at'])

    log(f'Physio library ready: course #{course.id}, {len(assets)} videos, {physio.packages.count()} empty packages.')
    log(f'New sessions created: {created}. Assign videos to packages in admin.')
    return course


def sync_course_packet(packet):
    """Keep catalog checkout rows in sync with a course packet."""
    from django.utils.text import slugify

    from catalog.models import CourseProduct, MediaAsset, Package, ProductKind
    from courses.models import Packet

    if packet is None or not getattr(packet, 'course_id', None):
        return None
    if not isinstance(packet, Packet):
        packet = Packet.objects.select_related('course').filter(pk=packet.pk).first()
        if packet is None:
            return None

    course = packet.course
    product = CourseProduct.objects.filter(
        linked_course=course, kind=ProductKind.PHYSIO_PACKAGES, is_active=True,
    ).first()
    if product is None:
        base = slugify(course.slug or course.title) or 'course'
        slug = f'{base}-packets'[:120]
        product = CourseProduct.objects.filter(slug=slug).first()
        if product is None:
            product = CourseProduct(
                kind=ProductKind.PHYSIO_PACKAGES,
                title=course.title,
                slug=slug,
                linked_course=course,
                is_active=True,
                bundle_enabled=False,
                expected_package_count=15,
            )
            product.save()
        else:
            product.linked_course = course
            product.kind = ProductKind.PHYSIO_PACKAGES
            product.bundle_enabled = False
            product.save(update_fields=['linked_course', 'kind', 'bundle_enabled', 'updated_at'])

    packet_count = course.packets.filter(is_active=True).count()
    if packet_count and product.expected_package_count < packet_count:
        product.expected_package_count = packet_count
        product.save(update_fields=['expected_package_count', 'updated_at'])

    defaults = {
        'product': product,
        'title': packet.title,
        'description': packet.description or '',
        'chapter_number': packet.order or 1,
        'individual_price': packet.price,
        'access_duration_days': packet.access_duration_days,
        'is_active': packet.is_active,
        'display_order': packet.order or 0,
    }
    package = Package.objects.filter(course_packet=packet).first()
    if package is None:
        package = (
            Package.objects.filter(product=product, chapter_number=packet.order).first()
            or Package.objects.filter(product=product, title__iexact=packet.title).first()
        )
        if package:
            package.course_packet = packet
            for field, value in defaults.items():
                setattr(package, field, value)
            package.save()
        else:
            package = Package(course_packet=packet, slug=f'packet-{packet.pk}', **defaults)
            package.save()
    else:
        for field, value in defaults.items():
            setattr(package, field, value)
        if packet.cover and not package.cover:
            package.cover = packet.cover
        package.save()

    keep_ids = []
    videos = packet.videos.filter(is_active=True).order_by('order', 'id')[: Packet.MAX_VIDEOS]
    for index, session in enumerate(videos, start=1):
        asset, _ = MediaAsset.objects.get_or_create(
            product=product,
            session=session,
            defaults={
                'package': package,
                'title': session.title,
                'description': session.description or '',
                'video_url': session.video_url or '',
                'duration_seconds': (session.duration or 0) * 60,
                'order': index,
                'is_active': True,
            },
        )
        asset.package = package
        asset.title = session.title
        if session.video_url:
            asset.video_url = session.video_url
        asset.order = index
        asset.is_active = True
        asset.save()
        keep_ids.append(asset.id)
    MediaAsset.objects.filter(package=package).exclude(pk__in=keep_ids).update(package=None)
    return package
