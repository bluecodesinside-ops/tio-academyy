from django.core.management.base import BaseCommand
from slideshow.models import SlideshowItem

class Command(BaseCommand):
    help = 'Sets up sample slideshow data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample slideshow data...')

        # Clear existing data
        SlideshowItem.objects.all().delete()

        # Create sample slideshow items
        slideshow_items = [
            {
                'title': 'Welcome to Tio Academy',
                'description': 'Experience the art of dance through our curated programs and distinguished instruction.',
                'media_type': 'image',
                'order': 1,
            },
            {
                'title': 'Salsa Dancing',
                'description': 'Master the passionate rhythms of Salsa with our expert instructors.',
                'media_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'order': 2,
            },
            {
                'title': 'Bachata Sensual',
                'description': 'Learn the sensual movements of Bachata in our intimate classes.',
                'media_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'order': 3,
            },
            {
                'title': 'Hip Hop Grooves',
                'description': 'Express yourself through energetic Hip Hop dance styles.',
                'media_type': 'video',
                'video_url': 'https://www.youtube.com/watch?v=3t_y_2_2_2_2',
                'order': 4,
            },
            {
                'title': 'Ballroom Elegance',
                'description': 'Discover the grace and elegance of Ballroom dancing.',
                'media_type': 'image',
                'order': 5,
            },
        ]

        for item_data in slideshow_items:
            SlideshowItem.objects.create(**item_data)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(slideshow_items)} slideshow items!'))

