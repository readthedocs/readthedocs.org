"""Project exceptions."""


from readthedocs.doc_builder.exceptions import BuildAppError, BuildUserError
from readthedocs.notifications.exceptions import NotificationBaseException


class ProjectConfigurationError(BuildUserError):

    """Error raised trying to configure a project for build."""

    NOT_FOUND = "project:sphinx:conf-py-not-found"
    MULTIPLE_CONF_FILES = "project:sphinx:multiple-conf-py-files-found"


class UserFileNotFound(BuildUserError):
    FILE_NOT_FOUND = "project:file:not-found"


class RepositoryError(BuildUserError):

    """Failure during repository operation."""

    CLONE_ERROR_WITH_PRIVATE_REPO_ALLOWED = "project:repository:private-clone-error"
    CLONE_ERROR_WITH_PRIVATE_REPO_NOT_ALLOWED = "project:repository:public-clone-error"
    DUPLICATED_RESERVED_VERSIONS = "project:repository:duplicated-reserved-versions"
    FAILED_TO_CHECKOUT = "project:repository:checkout-failed"
    GENERIC = "project:repository:generic-error"


class SyncRepositoryLocked(BuildAppError):

    """Error risen when there is another sync_repository_task already running."""

    REPOSITORY_LOCKED = "project:repository:locked"


class ProjectAutomaticCreationDisallowed(NotificationBaseException):

    """Used for raising messages in the project automatic create form view"""

    NO_CONNECTED_ACCOUNT = "project:create:automatic:no-connected-account"
    SSO_ENABLED = "project:create:automatic:sso-enabled"
    INADEQUATE_PERMISSIONS = "project:create:automatic:inadequate-permissions"


class ProjectManualCreationDisallowed(NotificationBaseException):

    """Used for raising messages in the project manual create form view"""

    SSO_ENABLED = "project:create:manual:sso-enabled"
    INADEQUATE_PERMISSIONS = "project:create:manual:inadequate-permissions"
