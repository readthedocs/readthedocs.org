from rest_framework import routers
from .views import ProjectViewSet, NotificationViewSet

router = routers.DefaultRouter()
router.register(r'project', ProjectViewSet)
router.register(r'notification', NotificationViewSet)
urlpatterns = router.urls