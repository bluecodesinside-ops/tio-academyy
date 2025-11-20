from django.core.management.base import BaseCommand
from gallery.models import Photo


class Command(BaseCommand):
    help = 'Add sample photos with Albanian translations for testing'

    def handle(self, *args, **options):
        # Sample photos with both English and Albanian content
        sample_photos = [
            {
                'title_en': 'Salsa Performance Night',
                'title_sq': 'Nata e Performancës së Salsës',
                'description_en': 'Amazing salsa performance showcasing advanced techniques and passionate dancing.',
                'description_sq': 'Performancë e mahnitshme salse duke treguar teknika të avancuara dhe kërcim pasionant.',
                'image_url': 'https://images.unsplash.com/photo-1547153760-18fc86324498?w=800&h=600&fit=crop'
            },
            {
                'title_en': 'Bachata Workshop',
                'title_sq': 'Punëtoria e Bachatës',
                'description_en': 'Students learning the sensual moves of bachata in our weekly workshop.',
                'description_sq': 'Studentët duke mësuar lëvizjet sensuale të bachatës në punëtorinë tonë javore.',
                'image_url': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&h=600&fit=crop'
            },
            {
                'title_en': 'Merengue Class Energy',
                'title_sq': 'Energjia e Klasës së Merengues',
                'description_en': 'High-energy merengue class with students from all skill levels.',
                'description_sq': 'Klasë me energji të lartë merengue me studentë nga të gjitha nivelet.',
                'image_url': 'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4?w=800&h=600&fit=crop'
            },
            {
                'title_en': 'Latin Dance Competition',
                'title_sq': 'Konkurs Kërcimi Latino',
                'description_en': 'Annual competition featuring our best dancers in various Latin styles.',
                'description_sq': 'Konkurs vjetor që paraqet kërcimtarët tanë më të mirë në stile të ndryshme latino.',
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop'
            }
        ]

        for photo_data in sample_photos:
            # Only use image_url and is_active, ignore all title/description fields
            existing = Photo.objects.filter(image_url=photo_data['image_url']).first()
            if not existing:
                photo = Photo.objects.create(
                    image_url=photo_data['image_url'],
                    is_active=True
                )
                self.stdout.write(f'✅ Created photo with image_url: {photo.image_url}')
            else:
                self.stdout.write(f'⚠️  Photo already exists: {photo_data["image_url"]}')

        self.stdout.write(self.style.SUCCESS('🖼️ Sample photos (no title/description) added!'))

