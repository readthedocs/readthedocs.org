from django.urls import path

from readthedocs.subscriptions.views import DetailSubscription, StripeCustomerPortal

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
