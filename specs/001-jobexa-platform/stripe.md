# Stripe Commercialization & Subscription Specification

This document defines the billing schema, payment integration, and subscription lifecycle management for the Jobexa platform using Stripe.

## Subscription Pricing Tiers

Jobexa offers three subscription plans to suit different user needs:

| Plan Tier | Price (USD) | Features | Draft Limit | Resume Limit | Automated Sending |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Basic (Free)** | $0.00 | Manual copy/drafts, basic parsing | 5 / month | 1 resume | ❌ No |
| **Pro** | $15.00/mo | Standard agent matching, automated email delivery | Unlimited | 5 resumes |  Yes (Gmail/SMTP) |
| **Premium** | $39.00/mo | ATS auto-optimization, dedicated agent autofills, priority queues | Unlimited | Unlimited |  Yes (Gmail/SMTP) |

---

## Database Schema Extensions

To track subscription statuses, the `users` table is extended with the following columns:

```sql
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN stripe_subscription_id VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(50) DEFAULT 'free' NOT NULL;
ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'active' NOT NULL;
```

---

## API Endpoints

### 1. Create Stripe Checkout Session
* **Endpoint**: `POST /api/v1/billing/create-checkout-session`
* **Request Payload**:
  ```json
  {
    "price_id": "price_1QxJobexaProXYZ"
  }
  ```
* **Response**:
  ```json
  {
    "checkout_url": "https://checkout.stripe.com/pay/cs_test_..."
  }
  ```

### 2. Webhook Event Listener
* **Endpoint**: `POST /api/v1/billing/webhook`
* **Security**: Stripe Signature Verification (`stripe-signature` header).
* **Supported Events**:
  * `checkout.session.completed`: Locates the user via `client_reference_id`, saves `stripe_customer_id`, updates tier to Pro/Premium.
  * `customer.subscription.updated` / `customer.subscription.deleted`: Syncs active/cancelled state to database.
