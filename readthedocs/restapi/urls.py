from django.conf.urls.defaults import url, patterns

from rest_framework import routers

from .views import ProjectViewSet, NotificationViewSet, VersionViewSet

router = routers.DefaultRouter()
router.register(r'version', VersionViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'notification', NotificationViewSet)

urlpatterns = patterns(
    '',
    url(r'footer_html/', 'restapi.views.footer_html', name='footer_html'),
    url(r'quick_search/', 'restapi.views.quick_search', name='quick_search'),
    url(r'index_search/', 'restapi.views.index_search', name='index_search'),
    url(r'search/', 'restapi.views.search', name='search'),
)
