"""Project exceptions."""

from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.doc_builder.exceptions import BuildUserError


class ProjectConfigurationError(BuildUserError):
    NOT_FOUND = "project:configuration:not-found"
    MULTIPLE_CONF_FILES = "project:configuration:multiple-conf-files"
    INVALID_VERSION = "project:configuration:invalid-version"
    INVALID = "project:configuration:invalid"
    MKDOCS_YAML_NOT_FOUND = "project:configuration:mkdocs-yaml-not-found"


class UserFileNotFound(BuildUserError):
    FILE_NOT_FOUND = "project:file:not-found"
    
class RepositoryError(BuildUserError):
    """Failure during repository operation."""

    CLONE_ERROR_WITH_PRIVATE_REPO_ALLOWED = "project:repository:private-clone-error"
    CLONE_ERROR_WITH_PRIVATE_REPO_NOT_ALLOWED = "project:repository:public-clone-error"
    DUPLICATED_RESERVED_VERSIONS = "project:repository:duplicated-reserved-versions"
    FAILED_TO_CHECKOUT = "project:repository:checkout-failed"
    GENERIC = "project:repository:generic-error"
    UNSUPPORTED_VCS = "project:repository:unsupported-vcs"


class SyncRepositoryLocked(BuildAppError):
    """Error risen when there is another sync_repository_task already running."""

    REPOSITORY_LOCKED = "project:repository:locked"
