import os
from django.core.management.base import BaseCommand
from gallery.models import Photo
from pathlib import Path

class Command(BaseCommand):
    help = 'Adds photos from the media directory to the database'

    def handle(self, *args, **options):
        media_dir = Path('media/gallery/photos')
        for subdir in [f.path for f in os.scandir(media_dir) if f.is_dir()]:
            category_name = os.path.basename(subdir)
            for filename in os.listdir(subdir):
                if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    try:
                        # Check if the photo already exists
                        photo_path = Path(subdir) / filename
                        if not Photo.objects.filter(image=photo_path).exists():
                            photo = Photo(title=filename, image=photo_path, description=category_name)
                            photo.save()
                            self.stdout.write(self.style.SUCCESS(f'Successfully added photo: {filename}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'Photo already exists: {filename}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding photo {filename}: {e}'))
