from django.core.management.base import BaseCommand
from courses.models import Session

class Command(BaseCommand):
    help = 'Test with a definitely public YouTube video to ensure embedding works'

    def handle(self, *args, **options):
        self.stdout.write('Testing with a public YouTube video...')
        
        # Use a definitely public YouTube video for testing
        test_video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Rick Roll - definitely public
        
        updated_count = 0
        
        # Update first few sessions to test
        test_sessions = Session.objects.all()[:5]
        
        for session in test_sessions:
            session.video_url = test_video_url
            session.save()
            updated_count += 1
            self.stdout.write(f'Updated: {session.title} with test video')
        
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} sessions with test video!'))
        self.stdout.write('Test video URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        self.stdout.write('This should definitely embed properly.')
