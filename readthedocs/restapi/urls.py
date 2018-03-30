"""Define routes between URL paths and views/endpoints."""

from __future__ import absolute_import

from django.conf.urls import url, include

from rest_framework import routers

from readthedocs.constants import pattern_opts
from readthedocs.comments.views import CommentViewSet
from readthedocs.restapi import views
from readthedocs.restapi.views import (
    core_views, footer_views, search_views, task_views, integrations
)

from .views.model_views import (BuildViewSet, BuildCommandViewSet,
                                ProjectViewSet, NotificationViewSet,
                                VersionViewSet, DomainViewSet,
                                RemoteOrganizationViewSet,
                                RemoteRepositoryViewSet,
                                SocialAccountViewSet)

router = routers.DefaultRouter()
router.register(r'build', BuildViewSet, base_name='build')
router.register(r'command', BuildCommandViewSet,
                base_name='buildcommandresult')
router.register(r'version', VersionViewSet, base_name='version')
router.register(r'project', ProjectViewSet, base_name='project')
router.register(r'notification', NotificationViewSet, base_name='emailhook')
router.register(r'domain', DomainViewSet, base_name='domain')
router.register(
    r'remote/org', RemoteOrganizationViewSet, base_name='remoteorganization')
router.register(
    r'remote/repo', RemoteRepositoryViewSet, base_name='remoterepository')
router.register(
    r'remote/account', SocialAccountViewSet, base_name='remoteaccount')
router.register(r'comments', CommentViewSet, base_name="comments")

urlpatterns = [
    url(r'^', include(router.urls)),
]

function_urls = [
    url(r'embed/', core_views.embed, name='embed'),
    url(r'docurl/', core_views.docurl, name='docurl'),
    url(r'cname/', core_views.cname, name='cname'),
    url(r'footer_html/', footer_views.footer_html, name='footer_html'),
]

search_urls = [
    url(r'index_search/',
        search_views.index_search,
        name='index_search'),
    url(r'search/$', views.search_views.search, name='api_search'),
    url(r'search/project/$',
        search_views.project_search,
        name='api_project_search'),
    url(r'search/section/$',
        search_views.section_search,
        name='api_section_search'),
]

task_urls = [
    url(r'jobs/status/(?P<task_id>[^/]+)/',
        task_views.job_status,
        name='api_job_status'),
    url(r'jobs/sync-remote-repositories/',
        task_views.sync_remote_repositories,
        name='api_sync_remote_repositories'),
]

integration_urls = [
    url(r'webhook/github/(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        integrations.GitHubWebhookView.as_view(),
        name='api_webhook_github'),
    url(r'webhook/gitlab/(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        integrations.GitLabWebhookView.as_view(),
        name='api_webhook_gitlab'),
    url(r'webhook/bitbucket/(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        integrations.BitbucketWebhookView.as_view(),
        name='api_webhook_bitbucket'),
    url(r'webhook/generic/(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        integrations.APIWebhookView.as_view(),
        name='api_webhook_generic'),
    url((r'webhook/(?P<project_slug>{project_slug})/'
         r'(?P<integration_pk>{integer_pk})/$'.format(**pattern_opts)),
        integrations.WebhookView.as_view(),
        name='api_webhook'),
]

urlpatterns += function_urls
urlpatterns += search_urls
urlpatterns += task_urls
urlpatterns += integration_urls

try:
    from readthedocsext.search.docsearch import DocSearch
    api_search_urls = [
        url(r'^docsearch/$', DocSearch.as_view(), name='doc_search'),
    ]
    urlpatterns += api_search_urls
except ImportError:
    pass

try:
    from readthedocsext.donate.restapi.urls import urlpatterns as sustainability_urls

    urlpatterns += [
        url(r'^sustainability/', include(sustainability_urls)),
    ]
except ImportError:
    pass
