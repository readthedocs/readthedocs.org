from rest_framework import routers

from .views import (
    ProjectsViewSet,
)

router = routers.DefaultRouter()
router.register(r'projects', ProjectsViewSet, basename='projects')

urlpatterns = router.urls
