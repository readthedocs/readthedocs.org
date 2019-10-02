"""Define routes between URL paths and views/endpoints."""

from django.conf import settings
from django.conf.urls import include, url
from rest_framework import routers

from readthedocs.api.v2.views import (
    core_views,
    footer_views,
    integrations,
    task_views,
)
from readthedocs.constants import pattern_opts
from readthedocs.sphinx_domains.api import SphinxDomainAPIView

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
router.register(r'sphinx_domain', SphinxDomainAPIView, basename='sphinxdomain')
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
    url(r'^', include(router.urls)),
]

function_urls = [
    url(r'docurl/', core_views.docurl, name='docurl'),
    url(r'footer_html/', footer_views.FooterHTML.as_view(), name='footer_html'),
]

task_urls = [
    url(
        r'jobs/status/(?P<task_id>[^/]+)/',
        task_views.job_status,
        name='api_job_status',
    ),
    url(
        r'jobs/sync-remote-repositories/',
        task_views.sync_remote_repositories,
        name='api_sync_remote_repositories',
    ),
]

integration_urls = [
    url(
        r'webhook/github/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.GitHubWebhookView.as_view(),
        name='api_webhook_github',
    ),
    url(
        r'webhook/gitlab/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.GitLabWebhookView.as_view(),
        name='api_webhook_gitlab',
    ),
    url(
        r'webhook/bitbucket/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.BitbucketWebhookView.as_view(),
        name='api_webhook_bitbucket',
    ),
    url(
        r'webhook/generic/(?P<project_slug>{project_slug})/$'.format(
            **pattern_opts
        ),
        integrations.APIWebhookView.as_view(),
        name='api_webhook_generic',
    ),
    url(
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

if 'readthedocsext.donate' in settings.INSTALLED_APPS:
    # pylint: disable=import-error
    from readthedocsext.donate.restapi.urls import urlpatterns \
        as sustainability_urls

    urlpatterns += [
        url(r'^sustainability/', include(sustainability_urls)),
    ]
