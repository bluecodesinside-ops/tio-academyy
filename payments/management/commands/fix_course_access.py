from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from payments.models import Payment, UserCourseAccess
from users.models import UserProfile


class Command(BaseCommand):
    help = 'Fix course access for users who have successful payments but missing access records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Fix 1: Ensure all users have profiles
        users_without_profiles = User.objects.filter(profile__isnull=True)
        if users_without_profiles.exists():
            self.stdout.write(f'Found {users_without_profiles.count()} users without profiles')
            if not dry_run:
                for user in users_without_profiles:
                    UserProfile.objects.get_or_create(user=user)
                self.stdout.write(self.style.SUCCESS('Created missing user profiles'))
        
        # Fix 2: Create missing UserCourseAccess records for successful payments
        successful_payments = Payment.objects.filter(status='succeeded')
        missing_access_count = 0
        
        for payment in successful_payments:
            if not UserCourseAccess.objects.filter(
                user=payment.user,
                course=payment.course,
                is_active=True
            ).exists():
                missing_access_count += 1
                if dry_run:
                    self.stdout.write(
                        f'Would create access for {payment.user.username} -> {payment.course.title}'
                    )
                else:
                    UserCourseAccess.objects.get_or_create(
                        user=payment.user,
                        course=payment.course,
                        defaults={'payment': payment, 'is_active': True}
                    )
                    self.stdout.write(
                        f'Created access for {payment.user.username} -> {payment.course.title}'
                    )
        
        if missing_access_count > 0:
            if dry_run:
                self.stdout.write(f'Found {missing_access_count} missing access records')
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Fixed {missing_access_count} missing access records')
                )
        else:
            self.stdout.write(self.style.SUCCESS('No missing access records found'))
        
        # Report summary
        total_users = User.objects.count()
        total_payments = Payment.objects.filter(status='succeeded').count()
        total_access = UserCourseAccess.objects.filter(is_active=True).count()
        
        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'Total users: {total_users}')
        self.stdout.write(f'Successful payments: {total_payments}')
        self.stdout.write(f'Active course access records: {total_access}')