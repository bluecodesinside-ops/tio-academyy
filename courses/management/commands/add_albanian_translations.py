from django.core.management.base import BaseCommand
from courses.models import Course, Level, Session


class Command(BaseCommand):
    help = 'Add Albanian translations to existing course content'

    def handle(self, *args, **options):
        # Define Albanian translations for courses
        course_translations = {
            'Salsa Fundamentals': {
                'title_sq': 'Bazat e Salsës',
                'description_sq': 'Mësoni lëvizjet bazë të salsës me instruktorë profesionalë. Kursi perfekt për fillestarë që duan të zotërojnë këtë kërcim pasionant latino.'
            },
            'Bachata Sensual': {
                'title_sq': 'Bachata Sensuale',
                'description_sq': 'Zbuloni sensualitetin dhe elegancën e bachatës. Mësoni teknika të avancuara lëvizjeje dhe interpretimi muzikor.'
            },
            'Merengue Express': {
                'title_sq': 'Merengue Express', 
                'description_sq': 'Kursi intensiv i merengues për të mësuar shpejt këtë kërcim energjik dominikan me ritëm të shpejtë.'
            },
            'Cumbia Colombiana': {
                'title_sq': 'Cumbia Kolumbiane',
                'description_sq': 'Eksploroni traditën e cumbias kolumbiane me lëvizje tradicionale dhe moderne të këtij kërcimi folklorik.'
            },
            'Reggaeton Urban': {
                'title_sq': 'Reggaeton Urban',
                'description_sq': 'Mësoni stilin urban të reggaetonit me lëvizje dinamike dhe expresive të këtij zhanri modern.'
            },
            'Latin Fusion': {
                'title_sq': 'Fuzion Latino',
                'description_sq': 'Kombinim i stileve të ndryshme latino në një kurs gjithëpërfshirës për dançues të përparuar.'
            }
        }

        # Level translations
        level_translations = {
            'Level 1': 'Niveli 1',
            'Level 2': 'Niveli 2', 
            'Level 3': 'Niveli 3',
            'Beginner': 'Fillestar',
            'Intermediate': 'Mesatar',
            'Advanced': 'I Përparuar'
        }

        # Update courses with Albanian translations
        courses = Course.objects.all()
        for course in courses:
            if course.title in course_translations:
                translation = course_translations[course.title]
                course.title_sq = translation['title_sq']
                course.description_sq = translation['description_sq']
                # Keep English as original
                if not course.title_en:
                    course.title_en = course.title
                if not course.description_en:
                    course.description_en = course.description
                course.save()
                self.stdout.write(f'✅ Updated course: {course.title} -> {course.title_sq}')

        # Update levels with Albanian translations  
        levels = Level.objects.all()
        for level in levels:
            if level.name in level_translations:
                level.name_sq = level_translations[level.name]
                # Keep English as original
                if not level.name_en:
                    level.name_en = level.name
                if level.description and not level.description_en:
                    level.description_en = level.description
                    level.description_sq = f'Përshkrimi për {level.name_sq}'
                level.save()
                self.stdout.write(f'✅ Updated level: {level.name} -> {level.name_sq}')

        # Update sessions with basic Albanian translations
        sessions = Session.objects.all()
        for session in sessions:
            if session.title and not session.title_sq:
                # Simple translation for session titles
                session.title_sq = f'Sesioni: {session.title}'
                if not session.title_en:
                    session.title_en = session.title
                
                if session.description and not session.description_sq:
                    session.description_sq = f'Mësim praktik për {session.title.lower()}'
                    if not session.description_en:
                        session.description_en = session.description
                
                session.save()
                self.stdout.write(f'✅ Updated session: {session.title} -> {session.title_sq}')

        self.stdout.write(self.style.SUCCESS('✨ Albanian translations added successfully!'))

