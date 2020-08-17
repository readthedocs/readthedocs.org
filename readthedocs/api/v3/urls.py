from .routers import DefaultRouterWithNesting
from .views import (
    BuildsCreateViewSet,
    BuildsViewSet,
    EnvironmentVariablesViewSet,
    ProjectsViewSet,
    RedirectsViewSet,
    SubprojectRelationshipViewSet,
    TranslationRelationshipViewSet,
    VersionsViewSet,
)


router = DefaultRouterWithNesting()

# allows /api/v3/projects/
# allows /api/v3/projects/pip/
# allows /api/v3/projects/pip/superproject/
# pylint: disable=assignment-from-no-return
projects = router.register(
    r'projects',
    ProjectsViewSet,
    basename='projects',
)

# allows /api/v3/projects/pip/subprojects/
subprojects = projects.register(
    r'subprojects',
    SubprojectRelationshipViewSet,
    basename='projects-subprojects',
    parents_query_lookups=['parent__slug'],
)

# allows /api/v3/projects/pip/translations/
translations = projects.register(
    r'translations',
    TranslationRelationshipViewSet,
    basename='projects-translations',
    parents_query_lookups=['main_language_project__slug'],
)

# allows /api/v3/projects/pip/versions/
# allows /api/v3/projects/pip/versions/latest/
versions = projects.register(
    r'versions',
    VersionsViewSet,
    basename='projects-versions',
    parents_query_lookups=['project__slug'],
)

# allows /api/v3/projects/pip/versions/v3.6.2/builds/
# allows /api/v3/projects/pip/versions/v3.6.2/builds/1053/
versions.register(
    r'builds',
    BuildsCreateViewSet,
    basename='projects-versions-builds',
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
    basename='projects-builds',
    parents_query_lookups=['project__slug'],
)

# allows /api/v3/projects/pip/redirects/
# allows /api/v3/projects/pip/redirects/1053/
projects.register(
    r'redirects',
    RedirectsViewSet,
    basename='projects-redirects',
    parents_query_lookups=['project__slug'],
)

# allows /api/v3/projects/pip/environmentvariables/
# allows /api/v3/projects/pip/environmentvariables/1053/
projects.register(
    r'environmentvariables',
    EnvironmentVariablesViewSet,
    basename='projects-environmentvariables',
    parents_query_lookups=['project__slug'],
)

urlpatterns = []
urlpatterns += router.urls
