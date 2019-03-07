from django.conf.urls import url

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .routers import DefaultRouterWithNesting
from .views import (
    BuildsViewSet,
    ProjectsViewSet,
    VersionsViewSet,
)

router = DefaultRouterWithNesting()

# allows /api/v3/projects/
# allows /api/v3/projects/pip/
projects = router.register(
    r'projects',
    ProjectsViewSet,
    basename='projects',
)

# allows /api/v3/projects/pip/versions/
# allows /api/v3/projects/pip/versions/latest/
versions = projects.register(
    r'versions',
    VersionsViewSet,
    base_name='projects-versions',
    parents_query_lookups=['project__slug'],
)

# allows /api/v3/projects/pip/versions/v3.6.2/builds/
# allows /api/v3/projects/pip/versions/v3.6.2/builds/1053/
versions.register(
    r'builds',
    BuildsViewSet,
    base_name='projects-versions-builds',
    parents_query_lookups=[
        'project__slug',
        'version__slug',
    ],
)

# allows /api/v3/projects/pip/builds/
# allows /api/v3/projects/pip/builds/1053/
projects.register(
    r'builds',
    BuildsViewSet,
    base_name='projects-builds',
    parents_query_lookups=['project__slug'],
)

urlpatterns = [
    url(r'^token/$', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    url(r'^token/refresh/$', TokenRefreshView.as_view(), name='token_refresh'),
    url(r'^token/verify/$', TokenVerifyView.as_view(), name='token_verify'),
]

urlpatterns += router.urls
