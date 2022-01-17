from django.conf.urls import re_path

from readthedocs.subscriptions.views import (
    DetailSubscription,
    StripeCustomerPortal,
)

urlpatterns = [
    re_path(
        r'^$',
        DetailSubscription.as_view(),
        name='subscription_detail',
    ),
    re_path(
        r'^portal$',
        StripeCustomerPortal.as_view(),
        name='stripe_customer_portal',
    ),
]
