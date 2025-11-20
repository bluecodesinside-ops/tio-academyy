from django.core.management.base import BaseCommand
from courses.models import Session

class Command(BaseCommand):
    help = 'Fix YouTube URLs to use standard watch format for better embedding'

    def handle(self, *args, **options):
        self.stdout.write('Fixing YouTube URLs for better embedding...')
        
        # Convert youtu.be URLs to youtube.com/watch format
        updated_count = 0
        
        sessions = Session.objects.filter(video_url__icontains='youtu.be')
        
        for session in sessions:
            old_url = session.video_url
            # Convert youtu.be/RYr96YYEaZY to youtube.com/watch?v=RYr96YYEaZY
            if 'youtu.be/' in old_url:
                video_id = old_url.split('youtu.be/')[1].split('?')[0]
                new_url = f'https://www.youtube.com/watch?v={video_id}'
                session.video_url = new_url
                session.save()
                updated_count += 1
                self.stdout.write(f'Updated: {session.title} - {old_url} -> {new_url}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} YouTube URLs!'))
        self.stdout.write('YouTube videos should now embed properly.')
