"""Constants for subscriptions."""
from djstripe.enums import SubscriptionStatus

# Days after the subscription has ended to disable the organization
DISABLE_AFTER_DAYS = 30

# These status are "terminal", meaning the subscription can't be updated.
# Users need to create a new subscription to use our service.
# https://stripe.com/docs/api/subscriptions/object#subscription_object-status.
TERMINAL_STRIPE_STATUS = [
    SubscriptionStatus.canceled,
    SubscriptionStatus.incomplete_expired,
]
