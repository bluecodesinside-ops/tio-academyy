from django.core.management.base import BaseCommand
from courses.models import Course, Level, Session

class Command(BaseCommand):
    help = 'Add YouTube video links to all sessions for testing'

    def handle(self, *args, **options):
        self.stdout.write('Adding YouTube video links to sessions...')
        
        # Sample YouTube videos for different dance styles
        youtube_videos = {
            'Salsa Fundamentals': {
                'Basic Steps': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Salsa Basic Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Salsa Basic Step Tutorial
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Salsa Basic Step Practice
                ],
                'Partner Work': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Salsa Partner Work
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Salsa Partner Patterns
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Salsa Partner Practice
                ],
                'Advanced Patterns': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Salsa Advanced Patterns
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Salsa Advanced Moves
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Salsa Advanced Practice
                ]
            },
            'Bachata Sensual': {
                'Basic Bachata': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Bachata Basic Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Bachata Basic Tutorial
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Bachata Basic Practice
                ],
                'Body Movement': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Bachata Body Movement
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Bachata Body Isolation
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Bachata Body Practice
                ],
                'Sensual Patterns': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Bachata Sensual Patterns
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Bachata Sensual Moves
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Bachata Sensual Practice
                ]
            },
            'Merengue Express': {
                'Merengue Basics': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Merengue Basic Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Merengue Basic Tutorial
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Merengue Basic Practice
                ],
                'Speed and Energy': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Merengue Speed Training
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Merengue Energy Moves
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Merengue Speed Practice
                ],
                'Advanced Merengue': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Merengue Advanced Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Merengue Advanced Moves
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Merengue Advanced Practice
                ]
            },
            'Cha Cha Cha': {
                'Cha Cha Basics': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Cha Cha Basic Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Cha Cha Basic Tutorial
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Cha Cha Basic Practice
                ],
                'Sharp Movements': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Cha Cha Sharp Moves
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Cha Cha Sharp Patterns
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Cha Cha Sharp Practice
                ],
                'Advanced Cha Cha': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Cha Cha Advanced Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Cha Cha Advanced Moves
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Cha Cha Advanced Practice
                ]
            },
            'Rumba Passion': {
                'Rumba Basics': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Rumba Basic Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Rumba Basic Tutorial
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Rumba Basic Practice
                ],
                'Passion and Expression': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Rumba Passion Moves
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Rumba Expression Training
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Rumba Passion Practice
                ],
                'Advanced Rumba': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Rumba Advanced Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Rumba Advanced Moves
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Rumba Advanced Practice
                ]
            },
            'Samba Carnival': {
                'Samba Basics': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Samba Basic Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Samba Basic Tutorial
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Samba Basic Practice
                ],
                'Carnival Moves': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Samba Carnival Moves
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Samba Carnival Patterns
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Samba Carnival Practice
                ],
                'Carnival Performance': [
                    'https://www.youtube.com/watch?v=J5Z4M7z2KqY',  # Samba Performance Steps
                    'https://www.youtube.com/watch?v=8Na9wP8Qx_I',  # Samba Performance Moves
                    'https://www.youtube.com/watch?v=QZ9vMj0_0tE',  # Samba Performance Practice
                ]
            }
        }
        
        updated_count = 0
        
        for course_title, levels in youtube_videos.items():
            try:
                course = Course.objects.get(title=course_title)
                self.stdout.write(f'Processing {course.title}...')
                
                for level_name, session_videos in levels.items():
                    try:
                        level = course.levels.get(name=level_name)
                        self.stdout.write(f'  Processing level: {level.name}')
                        
                        for i, video_url in enumerate(session_videos, 1):
                            try:
                                session = level.sessions.get(order=i)
                                session.video_url = video_url
                                session.save()
                                updated_count += 1
                                self.stdout.write(f'    Updated session {i}: {session.title}')
                            except Session.DoesNotExist:
                                self.stdout.write(f'    Session {i} not found in {level.name}')
                                
                    except Level.DoesNotExist:
                        self.stdout.write(f'  Level {level_name} not found in {course.title}')
                        
            except Course.DoesNotExist:
                self.stdout.write(f'Course not found: {course_title}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} sessions with YouTube links!'))
        self.stdout.write('Note: These are sample links. Replace with real dance tutorial videos.')
