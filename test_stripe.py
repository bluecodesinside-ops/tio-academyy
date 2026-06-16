#!/usr/bin/env python3
"""
Test script to verify Stripe integration is working
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
print("STRIPE INTEGRATION TEST")
print("=" * 60)

# Test 1: Check environment variables
print("\n1. Checking Environment Variables:")
print("-" * 60)
secret_key = settings.STRIPE_SECRET_KEY
publishable_key = settings.STRIPE_PUBLISHABLE_KEY
price_sub = settings.STRIPE_PRICE_SUB
price_onetime = settings.STRIPE_PRICE_ONE_TIME

print(f"STRIPE_SECRET_KEY: {'✓ SET' if secret_key else '✗ NOT SET'}")
if secret_key:
    print(f"  Key starts with: {secret_key[:7]}...")
    print(f"  Key type: {'LIVE' if secret_key.startswith('sk_live') else 'TEST' if secret_key.startswith('sk_test') else 'UNKNOWN'}")

print(f"\nSTRIPE_PUBLISHABLE_KEY: {'✓ SET' if publishable_key else '✗ NOT SET'}")
if publishable_key:
    print(f"  Key starts with: {publishable_key[:7]}...")
    print(f"  Key type: {'LIVE' if publishable_key.startswith('pk_live') else 'TEST' if publishable_key.startswith('pk_test') else 'UNKNOWN'}")

print(f"\nSTRIPE_PRICE_SUB: {'✓ SET' if price_sub and not 'your_' in price_sub else '✗ NOT SET (placeholder)'}")
if price_sub:
    print(f"  Value: {price_sub}")

print(f"\nSTRIPE_PRICE_ONE_TIME: {'✓ SET' if price_onetime and not 'your_' in price_onetime else '✗ NOT SET (placeholder)'}")
if price_onetime:
    print(f"  Value: {price_onetime}")

# Test 2: Test Stripe API connection
print("\n2. Testing Stripe API Connection:")
print("-" * 60)
if not secret_key:
    print("✗ Cannot test - Secret key not set")
else:
    try:
        stripe.api_key = secret_key
        # Try to retrieve account info (this is a safe API call)
        account = stripe.Account.retrieve()
        print(f"✓ Connected to Stripe successfully!")
        print(f"  Account ID: {account.id}")
        print(f"  Account type: {account.type}")
        print(f"  Country: {account.country}")
        print(f"  Charges enabled: {account.charges_enabled}")
        print(f"  Payouts enabled: {account.payouts_enabled}")
    except stripe.error.AuthenticationError as e:
        print(f"✗ Authentication failed: {e}")
        print("  Your secret key may be invalid")
    except stripe.error.APIConnectionError as e:
        print(f"✗ Connection error: {e}")
        print("  Check your internet connection")
    except Exception as e:
        print(f"✗ Error: {e}")

# Test 3: Test Price IDs (if set)
print("\n3. Testing Price IDs:")
print("-" * 60)
if price_sub and not 'your_' in price_sub:
    try:
        price = stripe.Price.retrieve(price_sub)
        print(f"✓ Subscription Price ID is valid!")
        print(f"  Price ID: {price.id}")
        print(f"  Amount: ${price.unit_amount/100} {price.currency.upper()}")
        print(f"  Type: {price.type}")
        print(f"  Active: {price.active}")
    except stripe.error.InvalidRequestError as e:
        print(f"✗ Subscription Price ID is invalid: {e}")
    except Exception as e:
        print(f"✗ Error checking subscription price: {e}")
else:
    print("✗ Subscription Price ID not configured (still using placeholder)")

if price_onetime and not 'your_' in price_onetime:
    try:
        price = stripe.Price.retrieve(price_onetime)
        print(f"✓ One-time Price ID is valid!")
        print(f"  Price ID: {price.id}")
        print(f"  Amount: ${price.unit_amount/100} {price.currency.upper()}")
        print(f"  Type: {price.type}")
        print(f"  Active: {price.active}")
    except stripe.error.InvalidRequestError as e:
        print(f"✗ One-time Price ID is invalid: {e}")
    except Exception as e:
        print(f"✗ Error checking one-time price: {e}")
else:
    print("✗ One-time Price ID not configured (still using placeholder)")

# Test 4: Summary
print("\n4. Summary:")
print("-" * 60)
issues = []
if not secret_key:
    issues.append("Secret key not set")
if not publishable_key:
    issues.append("Publishable key not set")
if not price_sub or 'your_' in price_sub:
    issues.append("Subscription price ID not configured")
if not price_onetime or 'your_' in price_onetime:
    issues.append("One-time price ID not configured")

if issues:
    print("⚠️  Issues found:")
    for issue in issues:
        print(f"   - {issue}")
    print("\n⚠️  ACTION REQUIRED:")
    print("   1. Add STRIPE_PRICE_SUB to .env (get from Stripe Dashboard → Products)")
    print("   2. Add STRIPE_PRICE_ONE_TIME to .env (get from Stripe Dashboard → Products)")
    print("   3. Restart Django server after updating .env")
else:
    print("✓ All configuration looks good!")
    print("  You can now test the checkout endpoints")

print("\n" + "=" * 60)

