from django.conf.urls import url, include

from rest_framework.documentation import include_docs_urls

from .routers import DefaultRouterWithNesting
from .views import (
    BuildsViewSet,
    ProjectsViewSet,
    VersionsViewSet,
    UsersViewSet,
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

projects.register(
    r'users',
    UsersViewSet,
    base_name='projects-users',
    parents_query_lookups=['projects__slug'],
)

urlpatterns = [
    url(r'^docs/', include_docs_urls(
        title='Read the Docs API',
        patterns=[
            url(r'/api/v3/', include(router.urls)),
        ],
        public=True),
    ),
]

urlpatterns += router.urls
