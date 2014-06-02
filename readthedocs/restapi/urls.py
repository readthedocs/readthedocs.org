from django.conf.urls import url, patterns

from rest_framework import routers

from .views.model_views import ProjectViewSet, NotificationViewSet, VersionViewSet

router = routers.DefaultRouter()
router.register(r'version', VersionViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'notification', NotificationViewSet)

urlpatterns = patterns(
    '',
	url(r'^', include(router.urls)),
    url(r'footer_html/', 'restapi.views.footer_views.footer_html', name='footer_html'),
    url(r'quick_search/', 'restapi.views.search_views.quick_search', name='quick_search'),
    url(r'index_search/', 'restapi.views.search_views.index_search', name='index_search'),
    url(r'search/$', 'restapi.views.search_views.search', name='search'),
    url(r'search/project/$', 'restapi.views.search_views.project_search', name='project_search'),
    url(r'search/section/$', 'restapi.views.search_views.section_search', name='section_search'),
)
