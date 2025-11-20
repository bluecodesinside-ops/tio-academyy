from django.core.management.base import BaseCommand
from courses.models import Session

class Command(BaseCommand):
    help = 'Update all sessions with the real dance tutorial video'

    def handle(self, *args, **options):
        self.stdout.write('Updating all sessions with real dance tutorial video...')
        
        # Real dance tutorial video URL - using the embed format
        real_video_url = 'https://www.youtube.com/watch?v=HyHNuVaZJ-k'
        
        updated_count = 0
        
        # Get all sessions and update them
        sessions = Session.objects.all()
        
        for session in sessions:
            session.video_url = real_video_url
            session.save()
            updated_count += 1
            self.stdout.write(f'Updated: {session.level.course.title} - {session.level.name} - {session.title}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} sessions with real dance tutorial video!'))
        self.stdout.write(f'Video URL: {real_video_url}')
        self.stdout.write('All sessions now have the same real dance tutorial video.')
