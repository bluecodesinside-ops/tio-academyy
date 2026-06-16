#!/usr/bin/env python3
"""
List all Stripe prices to help you find the right Price IDs
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
print("LISTING YOUR STRIPE PRICES")
print("=" * 60)

if not settings.STRIPE_SECRET_KEY:
    print("✗ Stripe secret key not set")
    sys.exit(1)

stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    # List all prices
    prices = stripe.Price.list(limit=100, active=True)
    
    if not prices.data:
        print("\n⚠️  No active prices found in your Stripe account.")
        print("\nTo create prices:")
        print("1. Go to https://dashboard.stripe.com/products")
        print("2. Click 'Add product'")
        print("3. Create a subscription product → Copy the Price ID")
        print("4. Create a one-time product → Copy the Price ID")
        print("5. Add them to your .env file")
    else:
        print(f"\n✓ Found {len(prices.data)} active price(s):\n")
        print("-" * 60)
        
        for price in prices.data:
            product = stripe.Product.retrieve(price.product)
            amount = price.unit_amount / 100 if price.unit_amount else 0
            currency = price.currency.upper()
            
            print(f"\nPrice ID: {price.id}")
            print(f"  Product: {product.name}")
            print(f"  Amount: ${amount} {currency}")
            print(f"  Type: {price.type}")
            print(f"  Recurring: {'Yes' if price.recurring else 'No'}")
            if price.recurring:
                print(f"    Interval: {price.recurring.interval}")
            print(f"  Active: {price.active}")
            print(f"  Created: {price.created}")
            print("-" * 60)
        
        print("\n💡 To use these prices:")
        print("   1. Copy the Price ID for your subscription product")
        print("   2. Copy the Price ID for your one-time product")
        print("   3. Add them to .env:")
        print("      STRIPE_PRICE_SUB=price_xxxxx")
        print("      STRIPE_PRICE_ONE_TIME=price_xxxxx")
        print("   4. Restart Django server")

except stripe.error.StripeError as e:
    print(f"✗ Stripe error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)

