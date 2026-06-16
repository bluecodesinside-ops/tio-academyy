from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile


class Command(BaseCommand):
    help = 'Create a demo user account for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='demo@tioacademy.com',
            help='Email for the demo user (default: demo@tioacademy.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='demo123',
            help='Password for the demo user (default: demo123)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists!')
            )
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Password: {password}')
            return
        
        # Create username from email
        username = email.split('@')[0]
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{email.split('@')[0]}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # UserProfile is created automatically via signal
        profile = UserProfile.objects.get(user=user)
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Demo user created successfully!')
        )
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write(f'  Email: {email}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write(f'  Username: {username}')
        self.stdout.write('')
        self.stdout.write('You can now login at: http://localhost:8000/login/')
        self.stdout.write('Dashboard: http://localhost:8000/dashboard/')

