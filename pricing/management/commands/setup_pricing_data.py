from django.core.management.base import BaseCommand
from pricing.models import PricingPackage, PaymentSettings, GuaranteeContent


class Command(BaseCommand):
    help = 'Sets up sample pricing data for the pricing system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample pricing data...')

        # Clear existing data
        PricingPackage.objects.all().delete()
        PaymentSettings.objects.all().delete()
        GuaranteeContent.objects.all().delete()

        # Create Pricing Packages
        standard_package = PricingPackage.objects.create(
            name='Standard',
            tier='standard',
            description='Perfect for beginners who want to start their dance journey',
            monthly_price=19.99,
            yearly_price=199.99,
            features=[
                'Access to Basic level videos',
                '5 downloads per month',
                'Email support',
                'Community forum access',
                'Progress tracking',
                'Mobile app access'
            ],
            is_popular=False,
            is_active=True,
            display_order=1,
            button_text='Choose Standard',
            stripe_monthly_price_id='price_standard_monthly_test',
            stripe_yearly_price_id='price_standard_yearly_test'
        )

        pro_package = PricingPackage.objects.create(
            name='Pro',
            tier='pro',
            description='For serious dancers who want to advance their skills',
            monthly_price=39.99,
            yearly_price=399.99,
            features=[
                'Access to Basic + Intermediate videos',
                'Unlimited downloads',
                'Priority email support',
                'Monthly live Q&A sessions',
                'Advanced progress tracking',
                'Exclusive Pro content',
                'Mobile app access',
                'Offline video access'
            ],
            is_popular=True,
            is_active=True,
            display_order=2,
            button_text='Choose Pro',
            stripe_monthly_price_id='price_pro_monthly_test',
            stripe_yearly_price_id='price_pro_yearly_test'
        )

        gold_package = PricingPackage.objects.create(
            name='Gold',
            tier='gold',
            description='Complete access for professional dancers and instructors',
            monthly_price=79.99,
            yearly_price=799.99,
            features=[
                'Access to ALL videos (Basic, Intermediate, Advanced)',
                'Unlimited downloads',
                '24/7 priority support',
                'Weekly live classes',
                '1-on-1 monthly coaching session',
                'Certificates of completion',
                'Personalized recommendations',
                'Advanced analytics',
                'Mobile app access',
                'Offline video access',
                'Early access to new content',
                'Instructor resources'
            ],
            is_popular=False,
            is_active=True,
            display_order=3,
            button_text='Choose Gold',
            stripe_monthly_price_id='price_gold_monthly_test',
            stripe_yearly_price_id='price_gold_yearly_test'
        )

        self.stdout.write(
            self.style.SUCCESS(f'Created {PricingPackage.objects.count()} pricing packages')
        )

        # Create Payment Settings
        payment_settings = PaymentSettings.objects.create(
            stripe_publishable_key='pk_test_your_publishable_key_here',
            stripe_secret_key='sk_test_your_secret_key_here',
            stripe_webhook_secret='whsec_your_webhook_secret_here',
            paypal_client_id='your_paypal_client_id',
            paypal_secret='your_paypal_secret',
            is_live_mode=False,
            success_redirect_url='/payment-success/',
            cancel_redirect_url='/pricing/'
        )

        self.stdout.write(
            self.style.SUCCESS('Created payment settings (test mode)')
        )

        # Create Guarantee Content
        guarantee_content = GuaranteeContent.objects.create(
            headline='100% Money-Back Guarantee',
            description='Try our program risk-free for 30 days. If you\'re not completely satisfied, we\'ll refund your money - no questions asked.',
            days=30,
            customer_count=10000,
            star_rating=4.8,
            is_active=True,
            icon='fas fa-shield-alt',
            background_color='#10B981'
        )

        self.stdout.write(
            self.style.SUCCESS('Created guarantee content')
        )

        # Display package information
        self.stdout.write('\n' + '='*50)
        self.stdout.write('PRICING PACKAGES CREATED:')
        self.stdout.write('='*50)
        
        for package in PricingPackage.objects.all().order_by('display_order'):
            self.stdout.write(f'\n{package.name} Package:')
            self.stdout.write(f'  Monthly: ${package.monthly_price}')
            self.stdout.write(f'  Yearly: ${package.yearly_price}')
            self.stdout.write(f'  Discount: {package.get_yearly_discount_percentage()}%')
            self.stdout.write(f'  Popular: {"Yes" if package.is_popular else "No"}')
            self.stdout.write(f'  Features: {len(package.get_features_list())}')

        self.stdout.write('\n' + '='*50)
        self.stdout.write('NEXT STEPS:')
        self.stdout.write('='*50)
        self.stdout.write('1. Update Stripe keys in Django admin (Payment Settings)')
        self.stdout.write('2. Create Stripe products and prices in Stripe Dashboard')
        self.stdout.write('3. Update stripe_price_id fields in packages')
        self.stdout.write('4. Test payment flow with Stripe test cards')
        self.stdout.write('5. Configure webhook endpoint: /pricing/webhooks/stripe/')
        
        self.stdout.write(
            self.style.SUCCESS('\nSuccessfully created sample pricing data!')
        )

