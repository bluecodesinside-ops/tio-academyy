#!/usr/bin/env python3
"""
Create $1 test products for real card testing
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

import stripe
from django.conf import settings

print("=" * 60)
print("CREATING $1 TEST PRODUCTS FOR REAL CARD TESTING")
print("=" * 60)

if not settings.STRIPE_SECRET_KEY:
    print("✗ Stripe secret key not set")
    sys.exit(1)

stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    # Create $1 Subscription Product
    print("\n1. Creating $1 Subscription Product...")
    print("-" * 60)
    
    subscription_product = stripe.Product.create(
        name="Test Subscription ($1)",
        description="Test subscription for $1/month - for testing purposes only",
    )
    
    subscription_price = stripe.Price.create(
        product=subscription_product.id,
        unit_amount=100,  # $1.00 in cents
        currency='usd',
        recurring={
            'interval': 'month',
        },
    )
    
    print(f"✓ $1 Subscription Product Created!")
    print(f"  Product ID: {subscription_product.id}")
    print(f"  Product Name: {subscription_product.name}")
    print(f"  Price ID: {subscription_price.id}")
    print(f"  Amount: ${subscription_price.unit_amount/100}/month")
    
    # Create $1 One-Time Product
    print("\n2. Creating $1 One-Time Product...")
    print("-" * 60)
    
    lifetime_product = stripe.Product.create(
        name="Test Lifetime Access ($1)",
        description="Test one-time payment for $1 - for testing purposes only",
    )
    
    lifetime_price = stripe.Price.create(
        product=lifetime_product.id,
        unit_amount=100,  # $1.00 in cents
        currency='usd',
    )
    
    print(f"✓ $1 One-Time Product Created!")
    print(f"  Product ID: {lifetime_product.id}")
    print(f"  Product Name: {lifetime_product.name}")
    print(f"  Price ID: {lifetime_price.id}")
    print(f"  Amount: ${lifetime_price.unit_amount/100} (one-time)")
    
    # Update .env file
    print("\n3. Updating .env file with $1 test prices...")
    print("-" * 60)
    
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # Read current .env
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Update price IDs
    lines = env_content.split('\n')
    updated_lines = []
    
    for line in lines:
        if line.startswith('STRIPE_PRICE_SUB='):
            updated_lines.append(f'STRIPE_PRICE_SUB={subscription_price.id}  # $1 test price')
        elif line.startswith('STRIPE_PRICE_ONE_TIME='):
            updated_lines.append(f'STRIPE_PRICE_ONE_TIME={lifetime_price.id}  # $1 test price')
        else:
            updated_lines.append(line)
    
    # Write back
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"✓ .env file updated!")
    print(f"  STRIPE_PRICE_SUB={subscription_price.id} ($1/month)")
    print(f"  STRIPE_PRICE_ONE_TIME={lifetime_price.id} ($1 one-time)")
    
    # Summary
    print("\n4. Summary:")
    print("-" * 60)
    print("✓ $1 test products created successfully!")
    print("\n📋 Test Products Created:")
    print(f"  1. Subscription: $1.00/month")
    print(f"     Price ID: {subscription_price.id}")
    print(f"  2. One-Time: $1.00")
    print(f"     Price ID: {lifetime_price.id}")
    print("\n⚠️  IMPORTANT:")
    print("  - These are LIVE prices - real charges will occur")
    print("  - Each test will charge $1 to your card")
    print("  - Restart Django server for changes to take effect")
    print("  - After testing, you can switch back to production prices")
    
except stripe.error.StripeError as e:
    print(f"\n✗ Stripe error: {e}")
    if hasattr(e, 'user_message'):
        print(f"  {e.user_message}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

