from rest_framework_extensions.routers import ExtendedSimpleRouter

from .views import (
    BuildsViewSet,
    ProjectsViewSet,
    VersionsViewSet,
)

router = ExtendedSimpleRouter()
projects = router.register(r'projects', ProjectsViewSet, basename='projects')
versions = projects.register(
    r'versions',
    VersionsViewSet,
    base_name='projects-versions',
    parents_query_lookups=['project__slug'],
)

# allows /api/v3/projects/pip/versions/v3.6.2/builds/
versions.register(
    r'builds',
    BuildsViewSet,
    base_name='projects-versions-builds',
    parents_query_lookups=[
        'project__slug',
        'version__slug',
    ],
)

projects.register(
    r'builds',
    BuildsViewSet,
    base_name='projects-builds',
    parents_query_lookups=['project__slug'],
)

urlpatterns = router.urls
