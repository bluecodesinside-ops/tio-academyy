from django.core.management.base import BaseCommand
from courses.models import Course, Level, Session

class Command(BaseCommand):
    help = 'Set up 6 courses with 3 levels and 3 sessions each'

    def handle(self, *args, **options):
        self.stdout.write('Setting up course structure...')
        
        # Course data
        courses_data = [
            {
                'title': 'Salsa Fundamentals',
                'description': 'Master the basics of salsa with step-by-step instruction from basic steps to advanced combinations.',
                'level': 'beginner',
                'price': 49.99,
                'rating': 4.8,
                'levels': [
                    {
                        'name': 'Basic Steps',
                        'description': 'Learn the fundamental salsa steps and rhythm.',
                        'sessions': [
                            {'title': 'Introduction to Salsa', 'description': 'Welcome to salsa! Learn about the history, music, and basic posture.'},
                            {'title': 'Basic Step Pattern', 'description': 'Master the essential forward-back step pattern that forms the foundation of salsa.'},
                            {'title': 'Side Steps and Weight Changes', 'description': 'Learn proper weight distribution and side step variations.'}
                        ]
                    },
                    {
                        'name': 'Partner Work',
                        'description': 'Learn to dance salsa with a partner using proper frame and connection.',
                        'sessions': [
                            {'title': 'Partner Frame and Connection', 'description': 'Establish proper frame and connection with your partner.'},
                            {'title': 'Basic Turn Pattern', 'description': 'Learn the fundamental right turn for both leader and follower.'},
                            {'title': 'Cross Body Lead', 'description': 'Master the essential cross body lead pattern.'}
                        ]
                    },
                    {
                        'name': 'Advanced Patterns',
                        'description': 'Combine all elements into beautiful, flowing dance patterns.',
                        'sessions': [
                            {'title': 'Combination Patterns', 'description': 'Learn to combine multiple moves into flowing sequences.'},
                            {'title': 'Styling and Body Movement', 'description': 'Add style and personality to your salsa dancing.'},
                            {'title': 'Performance Routine', 'description': 'Put it all together in a complete performance routine.'}
                        ]
                    }
                ]
            },
            {
                'title': 'Bachata Sensual',
                'description': 'Learn the romantic and sensual moves of bachata with fluid body movements and connection.',
                'level': 'intermediate',
                'price': 59.99,
                'rating': 4.9,
                'levels': [
                    {
                        'name': 'Basic Bachata',
                        'description': 'Learn the fundamental bachata steps and rhythm.',
                        'sessions': [
                            {'title': 'Bachata Basics', 'description': 'Introduction to bachata music, rhythm, and basic step pattern.'},
                            {'title': 'Side Steps and Weight Changes', 'description': 'Master weight distribution and side step variations in bachata.'},
                            {'title': 'Basic Partner Frame', 'description': 'Establish proper frame and connection for bachata.'}
                        ]
                    },
                    {
                        'name': 'Body Movement',
                        'description': 'Learn the sensual body movements that make bachata unique.',
                        'sessions': [
                            {'title': 'Hip Movement', 'description': 'Master the essential hip movement patterns in bachata.'},
                            {'title': 'Body Rolls and Waves', 'description': 'Learn fluid body rolls and wave movements.'},
                            {'title': 'Partner Body Movement', 'description': 'Coordinate body movements with your partner.'}
                        ]
                    },
                    {
                        'name': 'Sensual Patterns',
                        'description': 'Advanced sensual patterns and combinations.',
                        'sessions': [
                            {'title': 'Dips and Drops', 'description': 'Learn safe and beautiful dip and drop patterns.'},
                            {'title': 'Advanced Body Movement', 'description': 'Complex body movement combinations and styling.'},
                            {'title': 'Sensual Routine', 'description': 'Complete sensual bachata performance routine.'}
                        ]
                    }
                ]
            },
            {
                'title': 'Merengue Express',
                'description': 'High-energy merengue with fast-paced steps and exciting patterns.',
                'level': 'beginner',
                'price': 39.99,
                'rating': 4.7,
                'levels': [
                    {
                        'name': 'Merengue Basics',
                        'description': 'Learn the fundamental merengue steps and rhythm.',
                        'sessions': [
                            {'title': 'Merengue Introduction', 'description': 'Introduction to merengue music, history, and basic step.'},
                            {'title': 'Basic Step Variations', 'description': 'Learn different variations of the basic merengue step.'},
                            {'title': 'Partner Connection', 'description': 'Establish proper partner connection for merengue.'}
                        ]
                    },
                    {
                        'name': 'Speed and Energy',
                        'description': 'Build speed and energy in your merengue dancing.',
                        'sessions': [
                            {'title': 'Speed Training', 'description': 'Build speed and endurance for fast-paced merengue.'},
                            {'title': 'Energy and Expression', 'description': 'Add energy and expression to your merengue dancing.'},
                            {'title': 'Partner Speed Patterns', 'description': 'Fast-paced partner patterns and combinations.'}
                        ]
                    },
                    {
                        'name': 'Advanced Merengue',
                        'description': 'Advanced merengue patterns and performance techniques.',
                        'sessions': [
                            {'title': 'Complex Patterns', 'description': 'Learn complex merengue patterns and combinations.'},
                            {'title': 'Performance Techniques', 'description': 'Techniques for performing merengue on stage.'},
                            {'title': 'Merengue Showcase', 'description': 'Complete merengue performance routine.'}
                        ]
                    }
                ]
            },
            {
                'title': 'Cha Cha Cha',
                'description': 'Learn the playful and energetic cha cha cha with precise timing and sharp movements.',
                'level': 'intermediate',
                'price': 54.99,
                'rating': 4.6,
                'levels': [
                    {
                        'name': 'Cha Cha Basics',
                        'description': 'Learn the fundamental cha cha cha steps and timing.',
                        'sessions': [
                            {'title': 'Cha Cha Introduction', 'description': 'Introduction to cha cha cha music, rhythm, and basic step.'},
                            {'title': 'Cha Cha Timing', 'description': 'Master the distinctive cha cha cha timing and rhythm.'},
                            {'title': 'Basic Partner Work', 'description': 'Learn basic partner patterns in cha cha cha.'}
                        ]
                    },
                    {
                        'name': 'Sharp Movements',
                        'description': 'Develop sharp, precise movements characteristic of cha cha cha.',
                        'sessions': [
                            {'title': 'Sharp Steps', 'description': 'Learn sharp, precise step patterns and movements.'},
                            {'title': 'Body Isolation', 'description': 'Master body isolation techniques for cha cha cha.'},
                            {'title': 'Partner Sharp Patterns', 'description': 'Sharp and precise partner patterns.'}
                        ]
                    },
                    {
                        'name': 'Advanced Cha Cha',
                        'description': 'Advanced cha cha cha patterns and styling.',
                        'sessions': [
                            {'title': 'Complex Combinations', 'description': 'Learn complex cha cha cha combinations and patterns.'},
                            {'title': 'Styling and Expression', 'description': 'Add style and expression to your cha cha cha.'},
                            {'title': 'Cha Cha Performance', 'description': 'Complete cha cha cha performance routine.'}
                        ]
                    }
                ]
            },
            {
                'title': 'Rumba Passion',
                'description': 'Discover the passionate and romantic rumba with expressive body movements.',
                'level': 'advanced',
                'price': 69.99,
                'rating': 4.9,
                'levels': [
                    {
                        'name': 'Rumba Basics',
                        'description': 'Learn the fundamental rumba steps and expressive movements.',
                        'sessions': [
                            {'title': 'Rumba Introduction', 'description': 'Introduction to rumba music, history, and basic movements.'},
                            {'title': 'Expressive Body Movement', 'description': 'Learn expressive body movements fundamental to rumba.'},
                            {'title': 'Basic Partner Connection', 'description': 'Establish romantic partner connection for rumba.'}
                        ]
                    },
                    {
                        'name': 'Passion and Expression',
                        'description': 'Develop passionate expression and emotional connection.',
                        'sessions': [
                            {'title': 'Emotional Expression', 'description': 'Learn to express emotion through rumba movements.'},
                            {'title': 'Passionate Patterns', 'description': 'Romantic and passionate rumba patterns.'},
                            {'title': 'Partner Expression', 'description': 'Coordinate emotional expression with your partner.'}
                        ]
                    },
                    {
                        'name': 'Advanced Rumba',
                        'description': 'Advanced rumba techniques and performance artistry.',
                        'sessions': [
                            {'title': 'Advanced Techniques', 'description': 'Master advanced rumba techniques and movements.'},
                            {'title': 'Performance Artistry', 'description': 'Develop performance artistry and stage presence.'},
                            {'title': 'Rumba Masterpiece', 'description': 'Complete rumba performance masterpiece.'}
                        ]
                    }
                ]
            },
            {
                'title': 'Samba Carnival',
                'description': 'Experience the energy and excitement of Brazilian samba with carnival-style movements.',
                'level': 'advanced',
                'price': 74.99,
                'rating': 4.8,
                'levels': [
                    {
                        'name': 'Samba Basics',
                        'description': 'Learn the fundamental samba steps and carnival energy.',
                        'sessions': [
                            {'title': 'Samba Introduction', 'description': 'Introduction to samba music, carnival culture, and basic steps.'},
                            {'title': 'Carnival Energy', 'description': 'Learn to embody the energy and excitement of carnival samba.'},
                            {'title': 'Basic Samba Steps', 'description': 'Master the fundamental samba step patterns.'}
                        ]
                    },
                    {
                        'name': 'Carnival Moves',
                        'description': 'Learn authentic carnival samba movements and patterns.',
                        'sessions': [
                            {'title': 'Carnival Movements', 'description': 'Learn authentic carnival samba movements and styling.'},
                            {'title': 'Partner Carnival Patterns', 'description': 'Carnival-style partner patterns and combinations.'},
                            {'title': 'Energy and Stamina', 'description': 'Build energy and stamina for carnival-style samba.'}
                        ]
                    },
                    {
                        'name': 'Carnival Performance',
                        'description': 'Complete carnival samba performance with all elements.',
                        'sessions': [
                            {'title': 'Advanced Carnival', 'description': 'Advanced carnival samba techniques and patterns.'},
                            {'title': 'Performance Energy', 'description': 'Develop performance energy and carnival spirit.'},
                            {'title': 'Carnival Showcase', 'description': 'Complete carnival samba performance showcase.'}
                        ]
                    }
                ]
            }
        ]
        
        # Create courses
        for course_data in courses_data:
            course, created = Course.objects.get_or_create(
                title=course_data['title'],
                defaults={
                    'description': course_data['description'],
                    'level': course_data['level'],
                    'price': course_data['price'],
                    'rating': course_data['rating'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'Created course: {course.title}')
            else:
                self.stdout.write(f'Course already exists: {course.title}')
            
            # Create levels for this course
            for level_order, level_data in enumerate(course_data['levels'], 1):
                level, created = Level.objects.get_or_create(
                    course=course,
                    name=level_data['name'],
                    defaults={
                        'description': level_data['description'],
                        'order': level_order
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created level: {level.name}')
                
                # Create sessions for this level
                for session_order, session_data in enumerate(level_data['sessions'], 1):
                    session, created = Session.objects.get_or_create(
                        level=level,
                        title=session_data['title'],
                        defaults={
                            'description': session_data['description'],
                            'duration': 20,  # 20 minutes per session
                            'order': session_order,
                            'is_active': True,
                            'video_url': f'https://example.com/videos/{course.id}/{level.id}/{session_order}.mp4'
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'    Created session: {session.title}')
        
        self.stdout.write(self.style.SUCCESS('Successfully set up all courses with levels and sessions!'))
        self.stdout.write(f'Total courses: {Course.objects.count()}')
        self.stdout.write(f'Total levels: {Level.objects.count()}')
        self.stdout.write(f'Total sessions: {Session.objects.count()}')
