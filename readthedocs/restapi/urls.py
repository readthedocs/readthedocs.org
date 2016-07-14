from django.conf.urls import url, include

from rest_framework import routers

from .views.model_views import (BuildViewSet, BuildCommandViewSet,
                                ProjectViewSet, NotificationViewSet,
                                VersionViewSet, DomainViewSet,
                                RemoteOrganizationViewSet,
                                RemoteRepositoryViewSet)
from readthedocs.comments.views import CommentViewSet
from readthedocs.restapi import views
from readthedocs.restapi.views import (
    core_views, footer_views, search_views, task_views,
)

router = routers.DefaultRouter()
router.register(r'build', BuildViewSet)
router.register(r'command', BuildCommandViewSet)
router.register(r'version', VersionViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'notification', NotificationViewSet)
router.register(r'domain', DomainViewSet)
router.register(r'remote/org', RemoteOrganizationViewSet)
router.register(r'remote/repo', RemoteRepositoryViewSet)
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

urlpatterns += function_urls
urlpatterns += search_urls
urlpatterns += task_urls
