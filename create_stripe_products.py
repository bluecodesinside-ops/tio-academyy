#!/usr/bin/env python3
"""
Create Stripe products and prices for subscription and one-time payment
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
print("CREATING STRIPE PRODUCTS AND PRICES")
print("=" * 60)

if not settings.STRIPE_SECRET_KEY:
    print("✗ Stripe secret key not set")
    sys.exit(1)

stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    # Create Subscription Product
    print("\n1. Creating Subscription Product...")
    print("-" * 60)
    
    subscription_product = stripe.Product.create(
        name="Premium Subscription",
        description="Monthly subscription for unlimited access to all premium dance courses and content",
    )
    
    subscription_price = stripe.Price.create(
        product=subscription_product.id,
        unit_amount=2999,  # $29.99 in cents
        currency='usd',
        recurring={
            'interval': 'month',
        },
    )
    
    print(f"✓ Subscription Product Created!")
    print(f"  Product ID: {subscription_product.id}")
    print(f"  Product Name: {subscription_product.name}")
    print(f"  Price ID: {subscription_price.id}")
    print(f"  Amount: ${subscription_price.unit_amount/100}/month")
    
    # Create One-Time Product
    print("\n2. Creating One-Time Lifetime Access Product...")
    print("-" * 60)
    
    lifetime_product = stripe.Product.create(
        name="Lifetime Access",
        description="One-time payment for lifetime access to all premium dance courses and content",
    )
    
    lifetime_price = stripe.Price.create(
        product=lifetime_product.id,
        unit_amount=29999,  # $299.99 in cents
        currency='usd',
    )
    
    print(f"✓ Lifetime Access Product Created!")
    print(f"  Product ID: {lifetime_product.id}")
    print(f"  Product Name: {lifetime_product.name}")
    print(f"  Price ID: {lifetime_price.id}")
    print(f"  Amount: ${lifetime_price.unit_amount/100} (one-time)")
    
    # Update .env file
    print("\n3. Updating .env file...")
    print("-" * 60)
    
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # Read current .env
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Update or add price IDs
    lines = env_content.split('\n')
    updated_lines = []
    price_sub_found = False
    price_onetime_found = False
    
    for line in lines:
        if line.startswith('STRIPE_PRICE_SUB='):
            updated_lines.append(f'STRIPE_PRICE_SUB={subscription_price.id}')
            price_sub_found = True
        elif line.startswith('STRIPE_PRICE_ONE_TIME='):
            updated_lines.append(f'STRIPE_PRICE_ONE_TIME={lifetime_price.id}')
            price_onetime_found = True
        else:
            updated_lines.append(line)
    
    # Add if not found
    if not price_sub_found:
        updated_lines.append(f'STRIPE_PRICE_SUB={subscription_price.id}')
    if not price_onetime_found:
        updated_lines.append(f'STRIPE_PRICE_ONE_TIME={lifetime_price.id}')
    
    # Write back
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"✓ .env file updated!")
    print(f"  STRIPE_PRICE_SUB={subscription_price.id}")
    print(f"  STRIPE_PRICE_ONE_TIME={lifetime_price.id}")
    
    # Summary
    print("\n4. Summary:")
    print("-" * 60)
    print("✓ All products and prices created successfully!")
    print("\n📋 Created Products:")
    print(f"  1. Subscription: ${subscription_price.unit_amount/100}/month")
    print(f"     Price ID: {subscription_price.id}")
    print(f"  2. Lifetime Access: ${lifetime_price.unit_amount/100} (one-time)")
    print(f"     Price ID: {lifetime_price.id}")
    print("\n⚠️  IMPORTANT: Restart your Django server for changes to take effect!")
    print("   Run: python3 manage.py runserver")
    
except stripe.error.StripeError as e:
    print(f"\n✗ Stripe error: {e}")
    if hasattr(e, 'user_message'):
        print(f"  {e.user_message}")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

