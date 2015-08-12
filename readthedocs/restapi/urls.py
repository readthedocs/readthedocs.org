from django.conf.urls import url, patterns, include

from rest_framework import routers

from .views.model_views import BuildViewSet, ProjectViewSet, NotificationViewSet, VersionViewSet
from readthedocs.comments.views import CommentViewSet

router = routers.DefaultRouter()
router.register(r'build', BuildViewSet)
router.register(r'version', VersionViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'notification', NotificationViewSet)
router.register(r'comments', CommentViewSet, base_name="comments")

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
)

function_urls = patterns(
    '',
    url(r'embed/', 'readthedocs.restapi.views.core_views.embed', name='embed'),
    url(r'docurl/', 'readthedocs.restapi.views.core_views.docurl', name='docurl'),
    url(r'cname/', 'readthedocs.restapi.views.core_views.cname', name='cname'),
    url(r'footer_html/', 'readthedocs.restapi.views.footer_views.footer_html', name='footer_html'),
)

search_urls = patterns(
    '',
    url(r'index_search/',
        'readthedocs.restapi.views.search_views.index_search',
        name='index_search'),
    url(r'search/$', 'readthedocs.restapi.views.search_views.search', name='api_search'),
    url(r'search/project/$',
        'readthedocs.restapi.views.search_views.project_search',
        name='api_project_search'),
    url(r'search/section/$',
        'readthedocs.restapi.views.search_views.section_search',
        name='api_section_search'),
)

task_urls = patterns(
    '',
    url(r'jobs/status/(?P<task_id>[^/]+)/',
        'readthedocs.restapi.views.task_views.job_status',
        name='api_job_status'),
    url(r'jobs/sync-github-repositories/',
        'readthedocs.restapi.views.task_views.sync_github_repositories',
        name='api_sync_github_repositories'),
    url(r'jobs/sync-bitbucket-repositories/',
        'readthedocs.restapi.views.task_views.sync_bitbucket_repositories',
        name='api_sync_bitbucket_repositories'),
)


urlpatterns += function_urls
urlpatterns += search_urls
urlpatterns += task_urls
