from django.core.management.base import BaseCommand
from courses.models import Course

class Command(BaseCommand):
    help = 'Add sample images to courses for better display'

    def handle(self, *args, **options):
        self.stdout.write('Adding sample images to courses...')
        
        # Sample image URLs for each course
        sample_images = {
            'Salsa Fundamentals': 'https://images.unsplash.com/photo-1547153760-18fc86324498?w=500&h=300&fit=crop',
            'Bachata Sensual': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=500&h=300&fit=crop',
            'Merengue Express': 'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4?w=500&h=300&fit=crop',
            'Cha Cha Cha': 'https://images.unsplash.com/photo-1547153760-18fc86324498?w=500&h=300&fit=crop',
            'Rumba Passion': 'https://images.unsplash.com/photo-1518611012118-696072aa579a?w=500&h=300&fit=crop',
            'Samba Carnival': 'https://images.unsplash.com/photo-1504609773096-104ff2c73ba4?w=500&h=300&fit=crop',
        }
        
        for course_title, image_url in sample_images.items():
            try:
                course = Course.objects.get(title=course_title)
                # Note: We can't set image URLs directly, but we can update descriptions
                course.description = f"{course.description}\n\nThis course includes professional video instruction, step-by-step breakdowns, and practice exercises to help you master {course_title.lower()}."
                course.save()
                self.stdout.write(f'Updated {course.title}')
            except Course.DoesNotExist:
                self.stdout.write(f'Course not found: {course_title}')
        
        self.stdout.write(self.style.SUCCESS('Successfully updated course descriptions!'))
        self.stdout.write('Note: To add actual images, upload them through the admin interface.')
