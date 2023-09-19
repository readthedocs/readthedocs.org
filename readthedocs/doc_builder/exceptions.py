"""Exceptions raised when building documentation."""

from django.utils.translation import gettext_noop

from readthedocs.builds.constants import BUILD_STATE_CANCELLED
from readthedocs.projects.constants import BUILD_COMMANDS_OUTPUT_PATH_HTML


class BuildBaseException(Exception):
    message = None
    status_code = None

    def __init__(self, message=None, **kwargs):
        self.status_code = (
            kwargs.pop(
                "status_code",
                None,
            )
            or self.status_code
            or 1
        )
        self.message = message or self.message or self.get_default_message()
        super().__init__(message, **kwargs)

    def get_default_message(self):
        return self.message


class BuildAppError(BuildBaseException):
    GENERIC_WITH_BUILD_ID = gettext_noop(
        "There was a problem with Read the Docs while building your documentation. "
        "Please try again later. "
        "If this problem persists, "
        "report this error to us with your build id ({build_id}).",
    )


class BuildUserError(BuildBaseException):
    GENERIC = gettext_noop(
        "We encountered a problem with a command while building your project. "
        "To resolve this error, double check your project configuration and installed "
        "dependencies are correct and have not changed recently."
    )
    BUILD_COMMANDS_WITHOUT_OUTPUT = gettext_noop(
        f'No "{BUILD_COMMANDS_OUTPUT_PATH_HTML}" folder was created during this build.'
    )
    BUILD_OUTPUT_IS_NOT_A_DIRECTORY = gettext_noop(
        'Build output directory for format "{artifact_type}" is not a directory.'
    )
    BUILD_OUTPUT_HAS_0_FILES = gettext_noop(
        'Build output directory for format "{artifact_type}" does not contain any files. '
        "It seems the build process created the directory but did not save any file to it."
    )
    BUILD_OUTPUT_HAS_MULTIPLE_FILES = gettext_noop(
        'Build output directory for format "{artifact_type}" contains multiple files '
        "and it is not currently supported. "
        'Please, remove all the files but the "{artifact_type}" you want to upload.'
    )
    BUILD_OUTPUT_HTML_NO_INDEX_FILE = gettext_noop(
        "Your documentation did not generate an 'index.html' at its root directory. "
        "This is required for documentation serving at the root URL for this version."
    )
    BUILD_OUTPUT_OLD_DIRECTORY_USED = gettext_noop(
        "Some files were detected in an unsupported output path, '_build/html'. "
        "Ensure your project is configured to use the output path "
        "'$READTHEDOCS_OUTPUT/html' instead."
    )
    NO_CONFIG_FILE_DEPRECATED = gettext_noop(
        "The configuration file required to build documentation is missing from your project. "
        "Add a configuration file to your project to make it build successfully. "
        "Read more at https://docs.readthedocs.io/en/stable/config-file/v2.html"
    )
    BUILD_IMAGE_CONFIG_KEY_DEPRECATED = gettext_noop(
        'The configuration key "build.image" is deprecated. '
        'Use "build.os" instead to continue building your project. '
        "Read more at https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os"
    )
    BUILD_OS_REQUIRED = gettext_noop(
        'The configuration key "build.os" is required to build your documentation. '
        "Read more at https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os"
    )


class BuildUserSkip(BuildUserError):
    message = gettext_noop("This build was manually skipped using a command exit code.")
    state = BUILD_STATE_CANCELLED


class ProjectBuildsSkippedError(BuildUserError):
    message = gettext_noop("Builds for this project are temporarily disabled")


class YAMLParseError(BuildUserError):
    GENERIC_WITH_PARSE_EXCEPTION = gettext_noop(
        "Problem in your project's configuration. {exception}",
    )


class BuildMaxConcurrencyError(BuildUserError):
    message = gettext_noop(
        "Concurrency limit reached ({limit}), retrying in 5 minutes."
    )


class BuildCancelled(BuildUserError):
    message = gettext_noop("Build cancelled by user.")
    state = BUILD_STATE_CANCELLED


class PDFNotFound(BuildUserError):
    message = gettext_noop(
        'PDF file was not generated/found in "_readthedocs/pdf" output directory.'
    )


class MkDocsYAMLParseError(BuildUserError):
    GENERIC_WITH_PARSE_EXCEPTION = gettext_noop(
        "Problem parsing MkDocs YAML configuration. {exception}",
    )

    INVALID_DOCS_DIR_CONFIG = gettext_noop(
        'The "docs_dir" config from your MkDocs YAML config file has to be a '
        "string with relative or absolute path.",
    )

    INVALID_DOCS_DIR_PATH = gettext_noop(
        'The "docs_dir" config from your MkDocs YAML config file does not '
        "contain a valid path.",
    )

    INVALID_EXTRA_CONFIG = gettext_noop(
        'The "{config}" config from your MkDocs YAML config file has to be a '
        "list of relative paths.",
    )

    EMPTY_CONFIG = gettext_noop(
        "Please make sure the MkDocs YAML configuration file is not empty.",
    )
    NOT_FOUND = gettext_noop(
        "A configuration file was not found. "
        'Make sure you have a "mkdocs.yml" file in your repository.',
    )

    CONFIG_NOT_DICT = gettext_noop(
        "Your MkDocs YAML config file is incorrect. "
        "Please follow the user guide https://www.mkdocs.org/user-guide/configuration/ "
        "to configure the file properly.",
    )


# TODO: improve messages for symlink errors with a more detailed error and include the `filepath`.
class UnsupportedSymlinkFileError(BuildUserError):
    message = gettext_noop("Symlinks are not fully supported")


class FileIsNotRegularFile(UnsupportedSymlinkFileError):
    pass


class SymlinkOutsideBasePath(UnsupportedSymlinkFileError):
    pass


class FileTooLarge(BuildUserError):
    message = gettext_noop(
        "A file from your build process is too large to be processed by Read the Docs. "
        "Please ensure no files generated are larger than 1GB."
    )
