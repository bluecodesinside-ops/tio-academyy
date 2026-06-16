# Stripe Webhook Setup Guide

This guide explains how to set up and test Stripe webhooks for the Tio Academy platform.

## Webhook Endpoint

**Production URL:** `https://yourdomain.com/api/stripe/webhook/`  
**Local Testing URL:** `http://localhost:8000/api/stripe/webhook/`

## Environment Variables

Make sure these are set in your `.env` file:

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_SUB=price_...
STRIPE_PRICE_ONE_TIME=price_...
```

## Events Handled

The webhook handles the following Stripe events:

1. **`checkout.session.completed`**
   - Triggered when a customer completes a checkout session
   - Grants course access based on payment type (subscription or lifetime)
   - Updates `stripe_customer_id` and `stripe_subscription_id`

2. **`invoice.paid`**
   - Triggered when a subscription invoice is paid (renewals)
   - Activates subscription status to `active`
   - Ensures users maintain access after payment

3. **`customer.subscription.deleted`**
   - Triggered when a subscription is canceled
   - Sets subscription status to `canceled`
   - Revokes premium access (unless user has lifetime access)

4. **`customer.subscription.updated`**
   - Triggered when subscription status changes
   - Updates subscription status (active, past_due, trialing, etc.)

## Local Testing with Stripe CLI

### 1. Install Stripe CLI

**macOS:**
```bash
brew install stripe/stripe-cli/stripe
```

**Linux:**
```bash
wget https://github.com/stripe/stripe-cli/releases/latest/download/stripe_*_linux_x86_64.tar.gz
tar -xvf stripe_*_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/
```

**Windows:**
Download from: https://github.com/stripe/stripe-cli/releases

### 2. Login to Stripe CLI

```bash
stripe login
```

This will open your browser to authenticate with Stripe.

### 3. Forward Webhooks to Local Server

```bash
stripe listen --forward-to localhost:8000/api/stripe/webhook/
```

This command will:
- Start listening for webhook events
- Forward them to your local Django server
- Display a webhook signing secret (starts with `whsec_`)

**Important:** Copy the webhook signing secret and add it to your `.env` file:

```bash
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

### 4. Trigger Test Events

In a **new terminal window**, trigger test events:

```bash
# Test checkout.session.completed (subscription)
stripe trigger checkout.session.completed

# Test checkout.session.completed (one-time payment)
stripe trigger checkout.session.completed --override checkout_session:mode=payment

# Test invoice.paid
stripe trigger invoice.paid

# Test customer.subscription.deleted
stripe trigger customer.subscription.deleted

# Test customer.subscription.updated
stripe trigger customer.subscription.updated
```

### 5. Monitor Webhook Events

The Stripe CLI will show you:
- Event type
- Event ID
- HTTP status code (should be 200)
- Response time

Example output:
```
2024-01-15 10:30:45   --> checkout.session.completed [evt_xxx]
2024-01-15 10:30:45  <--  [200] POST http://localhost:8000/api/stripe/webhook/ [evt_xxx]
```

## Production Setup

### 1. Get Webhook Signing Secret

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Enter your production URL: `https://yourdomain.com/api/stripe/webhook/`
4. Select events to listen for:
   - `checkout.session.completed`
   - `invoice.paid`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
5. Copy the **Signing secret** (starts with `whsec_`)
6. Add it to your production `.env` file

### 2. Test Production Webhook

1. Make a test purchase in your production environment
2. Check Stripe Dashboard → Webhooks → Your endpoint → Events
3. Verify events are being received (green checkmark)
4. Check your Django logs to confirm events are processed

## Debugging

### Check Webhook Logs

The webhook logs important events. Check your Django logs:

```bash
# If using runserver
python manage.py runserver

# Check logs in production
tail -f /var/log/django/webhook.log
```

### Common Issues

1. **400 Bad Request**
   - Check that `STRIPE_WEBHOOK_SECRET` is set correctly
   - Verify the webhook signing secret matches Stripe Dashboard

2. **500 Internal Server Error**
   - Check that `STRIPE_SECRET_KEY` is set
   - Verify database connection
   - Check Django logs for errors

3. **User Not Found**
   - Ensure user exists in database
   - Check that `user_id` is in checkout session metadata
   - Verify email matches between Stripe and Django

4. **Events Not Received**
   - Verify webhook URL is correct
   - Check firewall/network settings
   - Ensure server is running and accessible

### Test User Identification

The webhook tries to find users in this order:
1. By `user_id` in checkout session metadata (preferred)
2. By `stripe_customer_id` in UserProfile
3. By email address from checkout session

## Verification

After setting up webhooks, verify:

1. ✅ User can complete checkout
2. ✅ Webhook receives `checkout.session.completed` event
3. ✅ User profile is updated with `subscription_status = 'active'` or `has_lifetime_access = True`
4. ✅ User can access premium course content
5. ✅ Subscription renewals trigger `invoice.paid` and maintain access
6. ✅ Subscription cancellations trigger `customer.subscription.deleted` and revoke access

## Security Notes

- **Never expose** `STRIPE_WEBHOOK_SECRET` in frontend code
- **Always verify** webhook signatures using `stripe.Webhook.construct_event()`
- **Use HTTPS** in production (Stripe requires it)
- **Keep webhook secret** in environment variables, never in code

## Additional Resources

- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)
- [Webhook Best Practices](https://stripe.com/docs/webhooks/best-practices)


