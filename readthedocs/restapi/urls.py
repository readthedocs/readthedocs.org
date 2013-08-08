from rest_framework import routers
from .views import ProjectViewSet

router = routers.DefaultRouter()
router.register(r'project', ProjectViewSet, base_name="project")
urlpatterns = router.urls