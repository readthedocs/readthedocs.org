from rest_framework_extensions.routers import ExtendedSimpleRouter

from .views import (
    ProjectsViewSet,
    VersionsViewSet,
)

router = ExtendedSimpleRouter()
router.register(r'projects', ProjectsViewSet, basename='projects') \
      .register(
          r'versions',
          VersionsViewSet,
          base_name='projects-versions',
          parents_query_lookups=['project__slug'],
      )

urlpatterns = router.urls
