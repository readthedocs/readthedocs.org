"""Define routes between URL paths and views/endpoints."""

from django.urls import include
from django.urls import path
from django.urls import re_path
from rest_framework import routers

from readthedocs.api.v2.views import core_views
from readthedocs.api.v2.views import integrations
from readthedocs.api.v2.views import task_views
from readthedocs.constants import pattern_opts

from .views.model_views import BuildCommandViewSet
from .views.model_views import BuildViewSet
from .views.model_views import DomainViewSet
from .views.model_views import NotificationViewSet
from .views.model_views import ProjectViewSet
from .views.model_views import RemoteOrganizationViewSet
from .views.model_views import RemoteRepositoryViewSet
from .views.model_views import SocialAccountViewSet
from .views.model_views import VersionViewSet


router = routers.DefaultRouter()
router.register(r"build", BuildViewSet, basename="build")
router.register(r"command", BuildCommandViewSet, basename="buildcommandresult")
router.register(r"version", VersionViewSet, basename="version")
router.register(r"project", ProjectViewSet, basename="project")
router.register(r"domain", DomainViewSet, basename="domain")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(
    r"remote/org",
    RemoteOrganizationViewSet,
    basename="remoteorganization",
)
router.register(
    r"remote/repo",
    RemoteRepositoryViewSet,
    basename="remoterepository",
)
router.register(
    r"remote/account",
    SocialAccountViewSet,
    basename="remoteaccount",
)

urlpatterns = [
    path("", include(router.urls)),
]

urlpatterns += [
    path(
        "revoke/",
        core_views.RevokeBuildAPIKeyView.as_view(),
        name="revoke_build_api_key",
    ),
]

function_urls = [
    path("docurl/", core_views.docurl, name="docurl"),
]

task_urls = [
    path(
        "jobs/status/<str:task_id>/",
        task_views.job_status,
        name="api_job_status",
    ),
    path(
        "jobs/sync-remote-repositories/",
        task_views.sync_remote_repositories,
        name="api_sync_remote_repositories",
    ),
]

integration_urls = [
    re_path(
        r"webhook/github/(?P<project_slug>{project_slug})/$".format(**pattern_opts),
        integrations.GitHubWebhookView.as_view(),
        name="api_webhook_github",
    ),
    re_path(
        r"webhook/gitlab/(?P<project_slug>{project_slug})/$".format(**pattern_opts),
        integrations.GitLabWebhookView.as_view(),
        name="api_webhook_gitlab",
    ),
    re_path(
        r"webhook/bitbucket/(?P<project_slug>{project_slug})/$".format(**pattern_opts),
        integrations.BitbucketWebhookView.as_view(),
        name="api_webhook_bitbucket",
    ),
    re_path(
        r"webhook/generic/(?P<project_slug>{project_slug})/$".format(**pattern_opts),
        integrations.APIWebhookView.as_view(),
        name="api_webhook_generic",
    ),
    re_path(
        (
            r"webhook/(?P<project_slug>{project_slug})/"
            r"(?P<integration_pk>{integer_pk})/$".format(**pattern_opts)
        ),
        integrations.WebhookView.as_view(),
        name="api_webhook",
    ),
]

urlpatterns += function_urls
urlpatterns += task_urls
urlpatterns += integration_urls
