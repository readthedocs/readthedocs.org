"""
Exceptions raised when building documentation.

Exceptions defined here have different categories based on

 - responsibility (user or application)
 - special cases (they need to be handled in a special way, e.g. concurrency limit reached)
 - grouped by topic (e.g. MkDocs errors)

All these exception should only define the "message id" under one of these categories.
Then the header/body texts should be defined in ``readthedocs/notifications/messages.py``.
"""

from django.utils.translation import gettext_lazy as _

from readthedocs.notifications.exceptions import NotificationBaseException


class BuildBaseException(NotificationBaseException):
    default_message = _("Build user exception")


class BuildAppError(BuildBaseException):
    default_message = _("Build application exception")

    GENERIC_WITH_BUILD_ID = "build:app:generic-with-build-id"
    UPLOAD_FAILED = "build:app:upload-failed"
    BUILDS_DISABLED = "build:app:project-builds-disabled"
    BUILD_DOCKER_UNKNOWN_ERROR = "build:app:docker:unknown-error"
    BUILD_TERMINATED_DUE_INACTIVITY = "build:app:terminated-due-inactivity"


class BuildUserError(BuildBaseException):
    GENERIC = "build:user:generic"

    BUILD_COMMANDS_WITHOUT_OUTPUT = "build:user:output:no-html"
    BUILD_OUTPUT_IS_NOT_A_DIRECTORY = "build:user:output:is-no-a-directory"
    BUILD_OUTPUT_HAS_0_FILES = "build:user:output:has-0-files"
    BUILD_OUTPUT_HAS_NO_PDF_FILES = "build:user:output:has-no-pdf-files"
    BUILD_OUTPUT_HAS_MULTIPLE_FILES = "build:user:output:has-multiple-files"
    BUILD_OUTPUT_HTML_NO_INDEX_FILE = "build:user:output:html-no-index-file"
    BUILD_OUTPUT_OLD_DIRECTORY_USED = "build:user:output:old-directory-used"
    FILE_TOO_LARGE = "build:user:output:file-too-large"
    TEX_FILE_NOT_FOUND = "build:user:tex-file-not-found"

    NO_CONFIG_FILE_DEPRECATED = "build:user:config:no-config-file"
    BUILD_IMAGE_CONFIG_KEY_DEPRECATED = "build:user:config:build-image-deprecated"
    BUILD_OS_REQUIRED = "build:user:config:build-os-required"

    BUILD_COMMANDS_IN_BETA = "build:user:build-commands-config-key-in-beta"
    BUILD_TIME_OUT = "build:user:time-out"
    BUILD_EXCESSIVE_MEMORY = "build:user:excessive-memory"
    VCS_DEPRECATED = "build:vcs:deprecated"

    SSH_KEY_WITH_WRITE_ACCESS = "build:user:ssh-key-with-write-access"


class BuildMaxConcurrencyError(BuildUserError):
    LIMIT_REACHED = "build:user:concurrency-limit-reached"


class BuildCancelled(BuildUserError):
    CANCELLED_BY_USER = "build:user:cancelled"
    SKIPPED_EXIT_CODE_183 = "build:user:exit-code-183"


class MkDocsYAMLParseError(BuildUserError):
    GENERIC_WITH_PARSE_EXCEPTION = "build:user:mkdocs:yaml-parse"
    INVALID_DOCS_DIR_CONFIG = "build:user:mkdocs:invalid-dir-config"
    INVALID_DOCS_DIR_PATH = "build:user:mkdocs:invalid-dir-path"
    INVALID_EXTRA_CONFIG = "build:user:mkdocs:invalid-extra-config"
    EMPTY_CONFIG = "build:user:mkdocs:empty-config"
    NOT_FOUND = "build:user:mkdocs:config-not-found"
    CONFIG_NOT_DICT = "build:user:mkdocs:invalid-yaml"
    SYNTAX_ERROR = "build:user:mkdocs:syntax-error"


# NOTE: there is no need to have three different error classes for this.
# We can merge all of them in one, always raise the same exception with different messages.
#
# TODO: improve messages for symlink errors with a more detailed error and include the `filepath`.
class UnsupportedSymlinkFileError(BuildUserError):
    SYMLINK_USED = "build:user:symlink:used"


class FileIsNotRegularFile(UnsupportedSymlinkFileError):
    pass


class SymlinkOutsideBasePath(UnsupportedSymlinkFileError):
    pass
