from django.urls import path

from readthedocs.subscriptions.views import DetailSubscription
from readthedocs.subscriptions.views import StripeCustomerPortal


urlpatterns = [
    path(
        "",
        DetailSubscription.as_view(),
        name="subscription_detail",
    ),
    path(
        "portal",
        StripeCustomerPortal.as_view(),
        name="stripe_customer_portal",
    ),
]
