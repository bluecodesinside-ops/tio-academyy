from django.core.management.base import BaseCommand
from programs.models import DanceStyle, Category, SkillLevel, Video


class Command(BaseCommand):
    help = 'Create sample data for the programs app'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for programs...')
        
        # Create Dance Styles
        latina_style, created = DanceStyle.objects.get_or_create(
            name='Latina',
            defaults={
                'description': 'Passionate and energetic Latin dance styles',
                'order': 1,
                'is_active': True
            }
        )
        
        hip_hop_style, created = DanceStyle.objects.get_or_create(
            name='Hip Hop',
            defaults={
                'description': 'Urban street dance with attitude and style',
                'order': 2,
                'is_active': True
            }
        )
        
        ballroom_style, created = DanceStyle.objects.get_or_create(
            name='Ballroom',
            defaults={
                'description': 'Elegant partner dances for formal occasions',
                'order': 3,
                'is_active': True
            }
        )
        
        # Create Categories for Latina
        salsa_category, created = Category.objects.get_or_create(
            dance_style=latina_style,
            name='Salsa',
            defaults={
                'description': 'The king of Latin dances with Cuban roots',
                'order': 1,
                'is_active': True
            }
        )
        
        bachata_category, created = Category.objects.get_or_create(
            dance_style=latina_style,
            name='Bachata',
            defaults={
                'description': 'Romantic Dominican dance with smooth movements',
                'order': 2,
                'is_active': True
            }
        )
        
        merengue_category, created = Category.objects.get_or_create(
            dance_style=latina_style,
            name='Merengue',
            defaults={
                'description': 'Fast-paced Dominican dance with marching steps',
                'order': 3,
                'is_active': True
            }
        )
        
        # Create Skill Levels for Salsa
        salsa_basic, created = SkillLevel.objects.get_or_create(
            category=salsa_category,
            level='basic',
            defaults={
                'description': 'Learn the fundamentals of salsa dancing',
                'order': 1,
                'is_active': True
            }
        )
        
        salsa_intermediate, created = SkillLevel.objects.get_or_create(
            category=salsa_category,
            level='intermediate',
            defaults={
                'description': 'Master complex patterns and styling',
                'order': 2,
                'is_active': True
            }
        )
        
        salsa_advanced, created = SkillLevel.objects.get_or_create(
            category=salsa_category,
            level='advanced',
            defaults={
                'description': 'Professional-level salsa techniques',
                'order': 3,
                'is_active': True
            }
        )
        
        # Create Videos for Salsa Basic
        Video.objects.get_or_create(
            skill_level=salsa_basic,
            title='Salsa Basic Steps - Introduction',
            defaults={
                'description': 'Learn the fundamental salsa basic steps and timing',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'duration': 300,  # 5 minutes
                'instructor_name': 'Tio Academy',
                'is_free': True,
                'price': 0.00,
                'order': 1,
                'is_active': True
            }
        )
        
        Video.objects.get_or_create(
            skill_level=salsa_basic,
            title='Salsa Basic Steps - Practice Session',
            defaults={
                'description': 'Practice session for salsa basic steps',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'duration': 450,  # 7.5 minutes
                'instructor_name': 'Tio Academy',
                'is_free': False,
                'price': 9.99,
                'order': 2,
                'is_active': True
            }
        )
        
        Video.objects.get_or_create(
            skill_level=salsa_basic,
            title='Salsa Basic Steps - Partner Work',
            defaults={
                'description': 'Learn to dance salsa with a partner',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'duration': 600,  # 10 minutes
                'instructor_name': 'Tio Academy',
                'is_free': False,
                'price': 9.99,
                'order': 3,
                'is_active': True
            }
        )
        
        # Create Videos for Salsa Intermediate
        Video.objects.get_or_create(
            skill_level=salsa_intermediate,
            title='Salsa Turns and Spins - Introduction',
            defaults={
                'description': 'Master the art of salsa turns and spins',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'duration': 480,  # 8 minutes
                'instructor_name': 'Tio Academy',
                'is_free': True,
                'price': 0.00,
                'order': 1,
                'is_active': True
            }
        )
        
        Video.objects.get_or_create(
            skill_level=salsa_intermediate,
            title='Salsa Styling Techniques',
            defaults={
                'description': 'Add style and personality to your salsa dancing',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'duration': 720,  # 12 minutes
                'instructor_name': 'Tio Academy',
                'is_free': False,
                'price': 12.99,
                'order': 2,
                'is_active': True
            }
        )
        
        # Create Videos for Bachata Basic
        bachata_basic, created = SkillLevel.objects.get_or_create(
            category=bachata_category,
            level='basic',
            defaults={
                'description': 'Learn the fundamentals of bachata dancing',
                'order': 1,
                'is_active': True
            }
        )
        
        Video.objects.get_or_create(
            skill_level=bachata_basic,
            title='Bachata Basic Steps - Introduction',
            defaults={
                'description': 'Learn the fundamental bachata basic steps',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'duration': 360,  # 6 minutes
                'instructor_name': 'Tio Academy',
                'is_free': True,
                'price': 0.00,
                'order': 1,
                'is_active': True
            }
        )
        
        Video.objects.get_or_create(
            skill_level=bachata_basic,
            title='Bachata Basic Steps - Practice',
            defaults={
                'description': 'Practice session for bachata basic steps',
                'video_url': 'https://www.youtube.com/watch?v=HyHNuVaZJ-k',
                'duration': 420,  # 7 minutes
                'instructor_name': 'Tio Academy',
                'is_free': False,
                'price': 9.99,
                'order': 2,
                'is_active': True
            }
        )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )
        self.stdout.write(f'Created {DanceStyle.objects.count()} dance styles')
        self.stdout.write(f'Created {Category.objects.count()} categories')
        self.stdout.write(f'Created {SkillLevel.objects.count()} skill levels')
        self.stdout.write(f'Created {Video.objects.count()} videos')

