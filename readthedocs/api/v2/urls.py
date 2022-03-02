"""Define routes between URL paths and views/endpoints."""

from django.conf import settings
from django.conf.urls import include, re_path
from rest_framework import routers

from readthedocs.api.v2.views import (
    core_views,
    footer_views,
    integrations,
    task_views,
)
from readthedocs.constants import pattern_opts
from readthedocs.gold.views import StripeEventView

from .views.model_views import (
    BuildCommandViewSet,
    BuildViewSet,
    DomainViewSet,
    ProjectViewSet,
    RemoteOrganizationViewSet,
    RemoteRepositoryViewSet,
    SocialAccountViewSet,
    VersionViewSet,
)


router = routers.DefaultRouter()
router.register(r'build', BuildViewSet, basename='build')
router.register(r'command', BuildCommandViewSet, basename='buildcommandresult')
router.register(r'version', VersionViewSet, basename='version')
router.register(r'project', ProjectViewSet, basename='project')
router.register(r'domain', DomainViewSet, basename='domain')
router.register(
    r'remote/org',
    RemoteOrganizationViewSet,
    basename='remoteorganization',
)
router.register(
    r'remote/repo',
    RemoteRepositoryViewSet,
    basename='remoterepository',
)
router.register(
    r'remote/account',
    SocialAccountViewSet,
    basename='remoteaccount',
)

urlpatterns = [
    re_path(r'^', include(router.urls)),
]

function_urls = [
    re_path(r'docurl/', core_views.docurl, name='docurl'),
    re_path(r'footer_html/', footer_views.FooterHTML.as_view(), name='footer_html'),
]

task_urls = [
    re_path(
        r'jobs/status/(?P<task_id>[^/]+)/',
        task_views.job_status,
        name='api_job_status',
    ),
    re_path(
        r'jobs/sync-remote-repositories/',
        task_views.sync_remote_repositories,
        name='api_sync_remote_repositories',
    ),
]

integration_urls = [
    re_path(
        r'webhook/github/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.GitHubWebhookView.as_view(),
        name='api_webhook_github',
    ),
    re_path(
        r'webhook/gitlab/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.GitLabWebhookView.as_view(),
        name='api_webhook_gitlab',
    ),
    re_path(
        r'webhook/bitbucket/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.BitbucketWebhookView.as_view(),
        name='api_webhook_bitbucket',
    ),
    re_path(
        r'webhook/generic/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.APIWebhookView.as_view(),
        name='api_webhook_generic',
    ),
    re_path(
        (
            r'webhook/(?P<project_slug>{project_slug})/'
            r'(?P<integration_pk>{integer_pk})/$'.format(**pattern_opts)
        ),
        integrations.WebhookView.as_view(),
        name='api_webhook',
    ),
]

urlpatterns += function_urls
urlpatterns += task_urls
urlpatterns += integration_urls
urlpatterns += [
    re_path(r'^webhook/stripe/', StripeEventView.as_view(), name='api_webhook_stripe'),
]

if 'readthedocsext.donate' in settings.INSTALLED_APPS:
    # pylint: disable=import-error
    from readthedocsext.donate.restapi.urls import (
        urlpatterns as sustainability_urls,
    )

    urlpatterns += [
        re_path(r'^sustainability/', include(sustainability_urls)),
    ]
