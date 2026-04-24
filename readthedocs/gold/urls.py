"""Gold subscription URLs."""

from django.urls import path
from django.urls import re_path

from readthedocs.gold import views
from readthedocs.projects.constants import PROJECT_SLUG_REGEX


urlpatterns = [
    path(
        "",
        views.GoldSubscription.as_view(),
        name="gold_detail",
    ),
    path(
        "subscription/checkout/create/",
        views.GoldCreateCheckoutSession.as_view(),
        name="gold_checkout_create",
    ),
    path(
        "subscription/portal/",
        views.GoldSubscriptionPortal.as_view(),
        name="gold_subscription_portal",
    ),
    path("projects/", views.GoldProjectsListCreate.as_view(), name="gold_projects"),
    re_path(
        (
            r"^projects/remove/(?P<project_slug>{project_slug})/$".format(
                project_slug=PROJECT_SLUG_REGEX,
            )
        ),
        views.GoldProjectRemove.as_view(),
        name="gold_projects_remove",
    ),
]
