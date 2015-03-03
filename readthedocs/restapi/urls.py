from django.conf.urls import url, patterns, include

from rest_framework import routers

from .views.model_views import BuildViewSet, ProjectViewSet, NotificationViewSet, VersionViewSet
from comments.views import CommentViewSet

router = routers.DefaultRouter()
router.register(r'build', BuildViewSet)
router.register(r'version', VersionViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'notification', NotificationViewSet)
router.register(r'comments', CommentViewSet, base_name="comments")

urlpatterns = patterns(
    '',
    url(r'^', include(router.urls)),
    url(r'embed/', 'restapi.views.core_views.embed', name='embed'),
    url(r'docurl/', 'restapi.views.core_views.docurl', name='docurl'),
    url(r'cname/', 'restapi.views.core_views.cname', name='cname'),
    url(r'footer_html/', 'restapi.views.footer_views.footer_html', name='footer_html'),
    url(r'quick_search/', 'restapi.views.search_views.quick_search', name='quick_search'),
    url(r'index_search/', 'restapi.views.search_views.index_search', name='index_search'),
    url(r'search/$', 'restapi.views.search_views.search', name='api_search'),
    url(r'search/project/$', 'restapi.views.search_views.project_search', name='api_project_search'),
    url(r'search/section/$', 'restapi.views.search_views.section_search', name='api_section_search'),
)
