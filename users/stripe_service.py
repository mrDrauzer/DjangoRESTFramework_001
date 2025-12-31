from decimal import Decimal
from typing import Dict, Any

import stripe
from django.conf import settings


class StripeServiceError(Exception):
    pass


def _init_stripe() -> None:
    api_key = settings.STRIPE_API_KEY
    if not api_key:
        raise StripeServiceError('Stripe API key is not configured (STRIPE_API_KEY)')
    stripe.api_key = api_key


def _wrap_stripe_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except stripe.error.AuthenticationError as e:
            raise StripeServiceError('Stripe authentication failed: invalid API key.') from e
        except stripe.error.InvalidRequestError as e:
            msg = getattr(e, "user_message", str(e))
            raise StripeServiceError(
                f'Stripe invalid request: {msg}'
            ) from e
        except stripe.error.RateLimitError as e:
            raise StripeServiceError('Stripe rate limit exceeded, try again later.') from e
        except stripe.error.APIConnectionError as e:
            raise StripeServiceError('Stripe connection error, please try again.') from e
        except stripe.error.APIError as e:
            raise StripeServiceError('Stripe API error, please try again.') from e
        except Exception as e:
            raise StripeServiceError(
                f'Unexpected Stripe error: {str(e)}'
            ) from e
    return wrapper


@_wrap_stripe_errors
def create_product(name: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    _init_stripe()
    product = stripe.Product.create(name=name, metadata=metadata or {})
    return product


@_wrap_stripe_errors
def create_price(product_id: str, amount: Decimal, currency: str | None = None) -> Dict[str, Any]:
    _init_stripe()
    curr = (currency or settings.STRIPE_CURRENCY).lower()
    # Stripe принимает сумму в минимальных единицах (cents/kopeks)
    unit_amount = int(Decimal(amount) * 100)
    if unit_amount <= 0:
        raise StripeServiceError('Amount must be greater than 0.')
    price = stripe.Price.create(product=product_id, unit_amount=unit_amount, currency=curr)
    return price


@_wrap_stripe_errors
def create_checkout_session(
    price_id: str,
    quantity: int = 1,
    success_url: str | None = None,
    cancel_url: str | None = None,
    mode: str = 'payment',
) -> Dict[str, Any]:
    _init_stripe()
    site = settings.SITE_URL.rstrip('/')
    success = success_url or f"{site}/payments/success"
    cancel = cancel_url or f"{site}/payments/cancel"
    session = stripe.checkout.Session.create(
        mode=mode,
        line_items=[{"price": price_id, "quantity": quantity}],
        success_url=success,
        cancel_url=cancel,
    )
    return session


@_wrap_stripe_errors
def retrieve_session(session_id: str) -> Dict[str, Any]:
    _init_stripe()
    session = stripe.checkout.Session.retrieve(session_id)
    return session
