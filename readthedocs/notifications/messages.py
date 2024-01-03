from django.utils.translation import gettext_noop as _

from readthedocs.doc_builder.exceptions import (
    BuildAppError,
    BuildCancelled,
    BuildMaxConcurrencyError,
    BuildUserError,
    MkDocsYAMLParseError,
)
from readthedocs.projects.constants import BUILD_COMMANDS_OUTPUT_PATH_HTML

from .constants import ERROR, INFO, NOTE, TIP, WARNING


class Message:
    def __init__(self, id, header, body, type, icon_classes=None):
        self.id = id
        self.header = header
        self.body = body
        self.type = type  # (ERROR, WARNING, INFO, NOTE, TIP)
        self.icon_classes = icon_classes
        self.format_values = {}

    def __repr__(self):
        return f"<Message: {self.id}>"

    def __str__(self):
        return f"Message: {self.id} | {self.header}"

    def set_format_values(self, format_values):
        self.format_values = format_values or {}

    def get_display_icon_classes(self):
        if self.icon_classes:
            return self.icon_classes

        # Default classes that apply to all the notifications
        classes = [
            "fas",
        ]

        if self.type == ERROR:
            classes.append("fa-circle-xmark")
        if self.type == WARNING:
            classes.append("fa-circle-exclamation")
        if self.type == INFO:
            classes.append("fa-circle-info")
        if self.type == NOTE:
            classes.append("fa-circle-info")
        if self.type == TIP:
            classes.append("fa-circle-info")

        return " ".join(classes)

    def get_rendered_header(self):
        return self.header.format(**self.format_values)

    def get_rendered_body(self):
        return self.body.format(**self.format_values)


# TODO: review the copy of these notifications/messages on PR review and adapt them.
# Most of them are copied from what we had in `readthedocs.doc_builder.exceptions`
# and slightly adapted to have a header and a better body.
BUILD_MESSAGES = [
    Message(
        id=BuildAppError.GENERIC_WITH_BUILD_ID,
        header=_("Unknown problem"),
        # Note the message receives the instance it's attached to
        # and could be use it to inject related data
        body=_(
            """
                There was a problem with Read the Docs while building your documentation.
                Please try again later.
                If this problem persists,
                report this error to us with your build id ({instance.pk}).
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.GENERIC,
        header=_("Unknown problem"),
        body=_(
            """
                We encountered a problem with a command while building your project.
                To resolve this error, double check your project configuration and installed
                dependencies are correct and have not changed recently.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildMaxConcurrencyError.LIMIT_REACHED,
        header=_("Maximum concurrency limit reached."),
        body=_(
            """
                Concurrency limit reached ({limit}), retrying in 5 minutes.
                """
        ),
        type=INFO,
    ),
    Message(
        id=BuildCancelled.CANCELLED_BY_USER,
        header=_("Build cancelled manually."),
        body=_(
            """
                The user has cancelled this build.
                """
        ),
        type=INFO,
    ),
    Message(
        id=BuildUserError.SKIPPED_EXIT_CODE_183,
        header=_("Build skipped manually."),
        body=_(
            """
                This build was skipped because
                one of the commands exited with code 183
                """
        ),
        type=INFO,
    ),
    Message(
        id=BuildAppError.BUILDS_DISABLED,
        header=_("Builds are temporary disabled for this project."),
        body=_(
            """
                This is due to excessive usage of our resources.
                Please, contact our support team if you think this is a mistake
                and builds should be re-enabled.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.MAX_CONCURRENCY,
        header=_("Concurrency limit reached"),
        body=_(
            """
                Your project, organization, or user is currently building the maximum concurrency builds allowed ({limit}).
                It will automatically retry in 5 minutes.
                """
        ),
        type=WARNING,
    ),
    Message(
        id=BuildUserError.BUILD_COMMANDS_WITHOUT_OUTPUT,
        header=_("No HTML content found"),
        body=_(
            f"""
                No "{BUILD_COMMANDS_OUTPUT_PATH_HTML}" folder was created during this build.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_IS_NOT_A_DIRECTORY,
        header=_("Build output directory is not a directory"),
        body=_(
            """
                Build output directory for format "{artifact_type}" is not a directory.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_HAS_0_FILES,
        header=_("Build output directory doesn't contain any file"),
        body=_(
            """
                Build output directory for format "{artifact_type}" does not contain any files.
                It seems the build process created the directory but did not save any file to it.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_HAS_MULTIPLE_FILES,
        header=_("Build output directory contains multiple files"),
        body=_(
            """
                Build output directory for format "{artifact_type}" contains multiple files
                and it is not currently supported.
                Please, remove all the files but the "{artifact_type}" you want to upload.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_HTML_NO_INDEX_FILE,
        header=_("Index file is not present in HTML output directory"),
        body=_(
            """
                Your documentation did not generate an 'index.html' at its root directory.
                This is required for documentation serving at the root URL for this version.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_OLD_DIRECTORY_USED,
        header=_("Your project is outputing files in an old directory"),
        body=_(
            """
                Some files were detected in an unsupported output path, '_build/html'.
                Ensure your project is configured to use the output path
                '$READTHEDOCS_OUTPUT/html' instead.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.NO_CONFIG_FILE_DEPRECATED,
        header=_("Your project doesn't have a <code>.readthedocs.yaml</code> file"),
        body=_(
            """
                The configuration file required to build documentation is missing from your project.
                Add a configuration file to your project to make it build successfully.
                Read more at https://docs.readthedocs.io/en/stable/config-file/v2.html
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_IMAGE_CONFIG_KEY_DEPRECATED,
        header=_("Configuration key <code>build.image</code> is deprecated"),
        body=_(
            """
                The configuration key "build.image" is deprecated.
                Use "build.os" instead to continue building your project.
                Read more at https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OS_REQUIRED,
        header=_("Configuration key <code>build.os</code> is required"),
        body=_(
            """
                The configuration key "build.os" is required to build your documentation.
                Read more at https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.FILE_TOO_LARGE,
        header=_("There is at least one file that exceeds the size limit"),
        body=_(
            """
                A file from your build process is too large to be processed by Read the Docs.
                Please ensure no generated files are larger than 1GB.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.FILE_TOO_LARGE,
        header=_("There is no PDF file in output directory"),
        body=_(
            f"""
                PDF file was not generated/found in "{BUILD_COMMANDS_OUTPUT_PATH_HTML}/pdf" output directory.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_COMMANDS_IN_BETA,
        header=_("Config key <code>build.commands</code> is in beta"),
        body=_(
            """
        <strong>The <code>"build.commands"</code> feature is in beta, and could have backwards incompatible changes while in beta.</strong>
        Read more at <a href=""https://docs.readthedocs.io/page/build-customization.html#override-the-build-process">our documentation</a> to find out its limitations and potential issues.
            """
        ),
        type=INFO,
    ),
]

BUILD_MKDOCS_MESSAGES = [
    Message(
        id=MkDocsYAMLParseError.GENERIC_WITH_PARSE_EXCEPTION,
        header=_(""),
        body=_(
            """
                Problem parsing MkDocs YAML configuration. {exception}
                """
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.INVALID_DOCS_DIR_CONFIG,
        header=_(""),
        body=_(
            """
    The "docs_dir" config from your MkDocs YAML config file has to be a
    string with relative or absolute path.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.INVALID_DOCS_DIR_PATH,
        header=_(""),
        body=_(
            """
                """
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.INVALID_EXTRA_CONFIG,
        header=_(""),
        body=_(
            """
    The "{config}" config from your MkDocs YAML config file has to be a
    list of relative paths.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.EMPTY_CONFIG,
        header=_(""),
        body=_(
            """
    Please make sure the MkDocs YAML configuration file is not empty.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.NOT_FOUND,
        header=_(""),
        body=_(
            """
    A configuration file was not found.
    Make sure you have a "mkdocs.yml" file in your repository.
                """
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.CONFIG_NOT_DICT,
        header=_(""),
        body=_(
            """
    Your MkDocs YAML config file is incorrect.
    Please follow the user guide https://www.mkdocs.org/user-guide/configuration/
    to configure the file properly.
                """
        ),
        type=ERROR,
    ),
]

class MessagesRegistry:
    def __init__(self):
        self.messages = {}

    def add(self, messages):
        if not isinstance(messages, list):
            if not isinstance(messages, Message):
                raise ValueError(
                    "A message should be instance of Message or a list of Messages."
                )

            messages = [messages]

        for message in messages:
            if message.id in messages:
                raise ValueError("A message with the same 'id' is already registered.")
            self.messages[message.id] = message

    def get(self, message_id):
        return self.messages.get(message_id)


registry = MessagesRegistry()
registry.add(BUILD_MKDOCS_MESSAGES)
registry.add(BUILD_MESSAGES)
