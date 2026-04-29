"""Gold subscription URLs."""

from django.urls import path

from readthedocs.gold import views


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
    path(
        "projects/remove/<slug:project_slug>/",
        views.GoldProjectRemove.as_view(),
        name="gold_projects_remove",
    ),
]
