from .routers import DefaultRouterWithNesting
from .views import BuildsViewSet, ProjectsViewSet, UsersViewSet, VersionsViewSet, SubprojectRelationshipViewSet, TranslationRelationshipViewSet


router = DefaultRouterWithNesting()

# allows /api/v3/projects/
# allows /api/v3/projects/pip/
# allows /api/v3/projects/pip/superproject/
projects = router.register(
    r'projects',
    ProjectsViewSet,
    basename='projects',
)

# allows /api/v3/projects/pip/subprojects/
subprojects = projects.register(
    r'subprojects',
    SubprojectRelationshipViewSet,
    base_name='projects-subprojects',
    parents_query_lookups=['superprojects__parent__slug'],
)

# allows /api/v3/projects/pip/translations/
translations = projects.register(
    r'translations',
    TranslationRelationshipViewSet,
    base_name='projects-translations',
    parents_query_lookups=['main_language_project__slug'],
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

# allows /api/v3/projects/pip/users/
# allows /api/v3/projects/pip/users/humitos/
projects.register(
    r'users',
    UsersViewSet,
    base_name='projects-users',
    parents_query_lookups=['projects__slug'],
)

urlpatterns = []
urlpatterns += router.urls
