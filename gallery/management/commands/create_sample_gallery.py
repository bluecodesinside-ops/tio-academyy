from django.core.management.base import BaseCommand
from gallery.models import Photo, Video, Location, MediaType

class Command(BaseCommand):
    help = 'Creates sample photos and videos for the gallery'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample gallery content...')

        # Sample photos with image URLs
        sample_photos = [
            {
                'title': 'Dance Performance 1',
                'description': 'Beautiful dance performance at our studio',
                'location': Location.LATINE_DHERMI.name,
                'image_url': 'https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 2',
                'description': 'Elegant dance moves captured in motion',
                'location': Location.LATINE_DRYMADHES.name,
                'image_url': 'https://images.unsplash.com/photo-1508700929628-666bc8bd84ea?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 3',
                'description': 'Passionate dance expression',
                'location': Location.LATINE_DURRES.name,
                'image_url': 'https://images.unsplash.com/photo-1518611012118-696083aa47dd?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 4',
                'description': 'Dynamic dance routine',
                'location': Location.LATINE_TIKI.name,
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 5',
                'description': 'Graceful dance movements',
                'location': Location.LATINE_DHERMI.name,
                'image_url': 'https://images.unsplash.com/photo-1547153760-18fc86324498?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 6',
                'description': 'Energetic dance showcase',
                'location': Location.LATINE_DRYMADHES.name,
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop'
            }
        ]

        # Create photos
        for photo_data in sample_photos:
            photo, created = Photo.objects.get_or_create(
                title=photo_data['title'],
                defaults={
                    'description': photo_data['description'],
                    'location': photo_data['location'],
                    'media_type': MediaType.PHOTO.name,
                    'image_url': photo_data['image_url'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'✓ Created photo: {photo.title}')
            else:
                self.stdout.write(f'Photo already exists: {photo.title}')

        # Sample videos
        sample_videos = [
            {
                'title': 'Dance Tutorial 1',
                'description': 'Learn basic dance moves with our instructor',
                'location': Location.LATINE_DHERMI.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 2',
                'description': 'Advanced dance techniques and combinations',
                'location': Location.LATINE_DRYMADHES.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Performance Video',
                'description': 'Full dance performance recording',
                'location': Location.LATINE_DURRES.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            }
        ]

        # Create videos
        for video_data in sample_videos:
            video, created = Video.objects.get_or_create(
                title=video_data['title'],
                defaults={
                    'description': video_data['description'],
                    'location': video_data['location'],
                    'media_type': MediaType.VIDEO.name,
                    'video_url': video_data['video_url'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'✓ Created video: {video.title}')
            else:
                self.stdout.write(f'Video already exists: {video.title}')

        self.stdout.write(self.style.SUCCESS('\n=== Sample Gallery Content Created Successfully! ==='))
        self.stdout.write(f'Total Photos: {Photo.objects.filter(is_active=True).count()}')
        self.stdout.write(f'Total Videos: {Video.objects.filter(is_active=True).count()}')
        self.stdout.write(self.style.WARNING(f'Gallery URL: http://localhost:8000/gallery/'))
        self.stdout.write(self.style.SUCCESS('\nYou can now test the gallery with real content!'))






