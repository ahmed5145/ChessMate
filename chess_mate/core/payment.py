"""
Payment processing module for ChessMate application.
"""

try:
    import stripe
except ImportError:
    raise ImportError(
        "Failed to import stripe. Please ensure stripe is installed: pip install stripe"
    )

from django.conf import settings

# Credit package definitions
CREDIT_PACKAGES = {
    'basic': {
        'name': 'Basic Package',
        'credits': 100,
        'price': 999  # in cents (9.99 USD)
    },
    'pro': {
        'name': 'Pro Package',
        'credits': 300,
        'price': 2499  # in cents (24.99 USD)
    },
    'premium': {
        'name': 'Premium Package',
        'credits': 1000,
        'price': 4999  # in cents (49.99 USD)
    }
}

class PaymentProcessor:
    @staticmethod
    def create_checkout_session(user_id, package_id, amount, credits):
        """Create a Stripe checkout session for credit purchase."""
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe secret key not configured")

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            # Convert amount to cents if it's in dollars
            amount_in_cents = int(amount * 100) if amount < 100 else amount
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': amount_in_cents,
                        'product_data': {
                            'name': f'ChessMate Credits - {credits} credits',
                            'description': f'Purchase {credits} analysis credits for ChessMate',
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{settings.PAYMENT_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=settings.PAYMENT_CANCEL_URL,
                metadata={
                    'user_id': user_id,
                    'package_id': package_id,
                    'credits': credits
                }
            )
            return checkout_session
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error creating checkout session: {str(e)}")

    @staticmethod
    def verify_payment(session_id):
        """Verify a payment session."""
        if not settings.STRIPE_SECRET_KEY:
            raise ValueError("Stripe secret key not configured")

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                return {
                    'amount': session.amount_total,
                    'credits': int(session.metadata.get('credits', 0))
                }
            return None
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error verifying payment: {str(e)}") 