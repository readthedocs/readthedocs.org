from .routers import DefaultRouterWithNesting
from .views import (
    BuildsCreateViewSet,
    BuildsViewSet,
    EnvironmentVariablesViewSet,
    NotificationsBuildViewSet,
    NotificationsForUserViewSet,
    NotificationsOrganizationViewSet,
    NotificationsProjectViewSet,
    NotificationsUserViewSet,
    OrganizationsViewSet,
    ProjectsViewSet,
    RedirectsViewSet,
    RemoteOrganizationViewSet,
    RemoteRepositoryViewSet,
    SubprojectRelationshipViewSet,
    TranslationRelationshipViewSet,
    UsersViewSet,
    VersionsViewSet,
)

router = DefaultRouterWithNesting()

# allows /api/v3/projects/
# allows /api/v3/projects/pip/
# allows /api/v3/projects/pip/superproject/
projects = router.register(
    r"projects",
    ProjectsViewSet,
    basename="projects",
)

# allows /api/v3/projects/pip/notifications/
projects.register(
    r"notifications",
    NotificationsProjectViewSet,
    basename="projects-notifications",
    parents_query_lookups=["project__slug"],
)

# allows /api/v3/projects/pip/subprojects/
subprojects = projects.register(
    r"subprojects",
    SubprojectRelationshipViewSet,
    basename="projects-subprojects",
    parents_query_lookups=["parent__slug"],
)

# allows /api/v3/projects/pip/translations/
translations = projects.register(
    r"translations",
    TranslationRelationshipViewSet,
    basename="projects-translations",
    parents_query_lookups=["main_language_project__slug"],
)

# allows /api/v3/projects/pip/versions/
# allows /api/v3/projects/pip/versions/latest/
versions = projects.register(
    r"versions",
    VersionsViewSet,
    basename="projects-versions",
    parents_query_lookups=["project__slug"],
)

# allows /api/v3/projects/pip/versions/v3.6.2/builds/
# allows /api/v3/projects/pip/versions/v3.6.2/builds/1053/
versions.register(
    r"builds",
    BuildsCreateViewSet,
    basename="projects-versions-builds",
    parents_query_lookups=[
        "project__slug",
        "version__slug",
    ],
)

# allows /api/v3/projects/pip/builds/
# allows /api/v3/projects/pip/builds/1053/
builds = projects.register(
    r"builds",
    BuildsViewSet,
    basename="projects-builds",
    parents_query_lookups=["project__slug"],
)

# NOTE: we are only listing notifications on APIv3 for now.
# The front-end will use this endpoint.
# allows /api/v3/projects/pip/builds/1053/notifications/
builds.register(
    r"notifications",
    NotificationsBuildViewSet,
    basename="projects-builds-notifications",
    parents_query_lookups=["project__slug", "build__id"],
)

# TODO: create an APIv3 endpoint to PATCH Build/Project notifications.
# This way the front-end can mark them as READ/DISMISSED.
#
# TODO: create an APIv3 endpoint to list notifications for Projects.

# allows /api/v3/projects/pip/redirects/
# allows /api/v3/projects/pip/redirects/1053/
projects.register(
    r"redirects",
    RedirectsViewSet,
    basename="projects-redirects",
    parents_query_lookups=["project__slug"],
)

# allows /api/v3/projects/pip/environmentvariables/
# allows /api/v3/projects/pip/environmentvariables/1053/
projects.register(
    r"environmentvariables",
    EnvironmentVariablesViewSet,
    basename="projects-environmentvariables",
    parents_query_lookups=["project__slug"],
)

# allows /api/v3/users/
users = router.register(
    r"users",
    UsersViewSet,
    basename="users",
)

users.register(
    r"notifications",
    NotificationsUserViewSet,
    basename="users-notifications",
    parents_query_lookups=["user__username"],
)

# allows /api/v3/organizations/
organizations = router.register(
    r"organizations",
    OrganizationsViewSet,
    basename="organizations",
)

organizations.register(
    r"notifications",
    NotificationsOrganizationViewSet,
    basename="organizations-notifications",
    parents_query_lookups=["organization__slug"],
)

# allows /api/v3/notifications/
router.register(
    r"notifications",
    NotificationsForUserViewSet,
    basename="notifications",
)

# allows /api/v3/remote/repositories/
router.register(
    r"remote/repositories",
    RemoteRepositoryViewSet,
    basename="remoterepositories",
)

# allows /api/v3/remote/organizations/
router.register(
    r"remote/organizations",
    RemoteOrganizationViewSet,
    basename="remoteorganizations",
)


urlpatterns = []
urlpatterns += router.urls
