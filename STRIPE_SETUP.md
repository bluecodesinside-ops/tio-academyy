# Stripe Payment Integration Setup Guide

## 🎯 Overview
This guide will help you set up Stripe payment processing for your Latina Dance Academy website. Users will be able to purchase courses using credit/debit cards.

## 🚀 Quick Setup

### 1. Create Stripe Account
1. Go to [https://stripe.com](https://stripe.com)
2. Sign up for a free account
3. Complete the account verification process

### 2. Get API Keys
1. Log into your Stripe Dashboard
2. Go to **Developers** → **API Keys**
3. Copy your **Publishable key** (starts with `pk_test_...`)
4. Copy your **Secret key** (starts with `sk_test_...`)

### 3. Set Environment Variables
Add these to your `.env` file or set them in your terminal:

```bash
# Stripe API Keys
export STRIPE_PUBLISHABLE_KEY="pk_test_your_publishable_key_here"
export STRIPE_SECRET_KEY="sk_test_your_secret_key_here"
export STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret_here"
```

### 4. Test the Integration
1. Start your Django server: `python3 manage.py runserver`
2. Go to a course page: `http://localhost:8000/course/1/`
3. Click "Purchase with Card" button
4. You'll be redirected to Stripe Checkout

## 💳 Test Cards

Use these test card numbers for testing:

| Card Number | Description |
|-------------|-------------|
| `4242 4242 4242 4242` | Visa - Success |
| `4000 0000 0000 0002` | Visa - Declined |
| `4000 0000 0000 9995` | Visa - Insufficient funds |
| `5555 5555 5555 4444` | Mastercard - Success |

**Test Details:**
- Use any future expiry date (e.g., 12/25)
- Use any 3-digit CVC (e.g., 123)
- Use any billing address

## 🔧 Features Implemented

### ✅ Payment Processing
- **Stripe Checkout**: Secure payment processing
- **Card Payments**: Accept all major credit/debit cards
- **Mobile Optimized**: Works on all devices

### ✅ Course Access Control
- **Purchase Tracking**: Track who bought what
- **Access Management**: Grant/revoke course access
- **Free Courses**: Free courses accessible to everyone

### ✅ User Experience
- **One-Click Purchase**: Simple checkout process
- **Progress Tracking**: Track learning progress
- **Purchase History**: View past purchases in admin

### ✅ Security
- **Webhook Verification**: Secure payment confirmation
- **CSRF Protection**: Prevent cross-site attacks
- **Access Control**: Only paid users can access content

## 📊 Admin Features

### Payment Management
- View all payments in Django admin
- Track payment status (pending, succeeded, failed)
- Monitor course access grants

### User Access
- See which users have access to which courses
- Grant/revoke access manually if needed
- Track access history

## 🚨 Important Notes

### Development vs Production
- **Development**: Use test keys (`pk_test_...`, `sk_test_...`)
- **Production**: Use live keys (`pk_live_...`, `sk_live_...`)

### Webhook Setup (Production)
1. Go to Stripe Dashboard → **Developers** → **Webhooks**
2. Add endpoint: `https://yourdomain.com/payments/webhook/`
3. Select events: `checkout.session.completed`
4. Copy the webhook secret to your environment variables

### Security
- Never commit API keys to version control
- Use environment variables for all sensitive data
- Enable webhook signature verification

## 🐛 Troubleshooting

### Common Issues

**"No checkout URL received"**
- Check if Stripe API keys are set correctly
- Verify the course exists and has a price

**"Payment failed"**
- Check Stripe dashboard for error details
- Verify webhook endpoint is accessible

**"Course not accessible after payment"**
- Check webhook is working correctly
- Verify UserCourseAccess record was created

### Debug Mode
Add this to your settings.py for debugging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Next Steps

1. **Set up webhooks** for production
2. **Configure email notifications** for successful payments
3. **Add subscription support** for recurring payments
4. **Implement refunds** and cancellations
5. **Add analytics** for payment tracking

## 🆘 Support

- **Stripe Documentation**: [https://stripe.com/docs](https://stripe.com/docs)
- **Django Stripe Integration**: [https://stripe.com/docs/checkout/django](https://stripe.com/docs/checkout/django)
- **Test Cards**: [https://stripe.com/docs/testing](https://stripe.com/docs/testing)

---

**🎉 Congratulations!** Your website now accepts card payments through Stripe!


