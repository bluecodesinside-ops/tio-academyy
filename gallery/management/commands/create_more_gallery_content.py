from django.core.management.base import BaseCommand
from gallery.models import Photo, Video, Location, MediaType

class Command(BaseCommand):
    help = 'Creates more sample photos and videos for pagination testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating additional gallery content for pagination...')

        # Create more photos to ensure we have at least 15+ photos
        additional_photos = [
            {
                'title': 'Dance Performance 7',
                'description': 'Elegant dance moves in perfect harmony',
                'location': Location.LATINE_DHERMI.name,
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 8',
                'description': 'Passionate expression through movement',
                'location': Location.LATINE_DRYMADHES.name,
                'image_url': 'https://images.unsplash.com/photo-1508700929628-666bc8bd84ea?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 9',
                'description': 'Dynamic choreography with energy',
                'location': Location.LATINE_DURRES.name,
                'image_url': 'https://images.unsplash.com/photo-1518611012118-696083aa47dd?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 10',
                'description': 'Graceful movements and perfect timing',
                'location': Location.LATINE_TIKI.name,
                'image_url': 'https://images.unsplash.com/photo-1547153760-18fc86324498?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 11',
                'description': 'Sensual dance with emotional depth',
                'location': Location.LATINE_DHERMI.name,
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 12',
                'description': 'High-energy performance with crowd interaction',
                'location': Location.LATINE_DRYMADHES.name,
                'image_url': 'https://images.unsplash.com/photo-1508700929628-666bc8bd84ea?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 13',
                'description': 'Professional dance showcase',
                'location': Location.LATINE_DURRES.name,
                'image_url': 'https://images.unsplash.com/photo-1518611012118-696083aa47dd?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 14',
                'description': 'Artistic expression through dance',
                'location': Location.LATINE_TIKI.name,
                'image_url': 'https://images.unsplash.com/photo-1547153760-18fc86324498?w=800&h=600&fit=crop'
            },
            {
                'title': 'Dance Performance 15',
                'description': 'Synchronized group performance',
                'location': Location.LATINE_DHERMI.name,
                'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop'
            }
        ]

        # Create more videos to ensure we have at least 12+ videos
        additional_videos = [
            {
                'title': 'Dance Tutorial 4',
                'description': 'Advanced footwork techniques and combinations',
                'location': Location.LATINE_DHERMI.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 5',
                'description': 'Partner work and connection exercises',
                'location': Location.LATINE_DRYMADHES.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 6',
                'description': 'Musicality and rhythm training',
                'location': Location.LATINE_DURRES.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 7',
                'description': 'Styling and personal expression',
                'location': Location.LATINE_TIKI.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 8',
                'description': 'Performance techniques and stage presence',
                'location': Location.LATINE_DHERMI.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 9',
                'description': 'Choreography breakdown and practice',
                'location': Location.LATINE_DRYMADHES.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 10',
                'description': 'Body isolation and control exercises',
                'location': Location.LATINE_DURRES.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 11',
                'description': 'Spinning techniques and balance',
                'location': Location.LATINE_TIKI.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'title': 'Dance Tutorial 12',
                'description': 'Social dancing etiquette and tips',
                'location': Location.LATINE_DHERMI.name,
                'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            }
        ]

        # Create additional photos
        for photo_data in additional_photos:
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

        # Create additional videos
        for video_data in additional_videos:
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

        self.stdout.write(self.style.SUCCESS('\n=== Additional Gallery Content Created! ==='))
        self.stdout.write(f'Total Photos: {Photo.objects.filter(is_active=True).count()}')
        self.stdout.write(f'Total Videos: {Video.objects.filter(is_active=True).count()}')
        self.stdout.write(self.style.WARNING(f'Gallery URL: http://localhost:8000/gallery/'))
        self.stdout.write(self.style.SUCCESS('\nNow you have enough content for pagination testing!'))


