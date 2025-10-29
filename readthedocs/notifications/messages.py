import copy
import textwrap

import structlog
from django.template import Context
from django.template import Template
from django.utils.translation import gettext_noop as _

from readthedocs.core.context_processors import readthedocs_processor
from readthedocs.doc_builder.exceptions import BuildAppError
from readthedocs.doc_builder.exceptions import BuildCancelled
from readthedocs.doc_builder.exceptions import BuildMaxConcurrencyError
from readthedocs.doc_builder.exceptions import BuildUserError
from readthedocs.doc_builder.exceptions import MkDocsYAMLParseError
from readthedocs.projects.constants import BUILD_COMMANDS_OUTPUT_PATH_HTML

from .constants import ERROR
from .constants import INFO
from .constants import NOTE
from .constants import TIP
from .constants import WARNING


log = structlog.get_logger(__name__)


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
        self.format_values = format_values

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

    def _prepend_template_prefix(self, template):
        """
        Prepend Django {% load %} template tag.

        This is required to render the notifications with custom filters/tags.
        """
        prefix = "{% load notifications_filters %}"
        return prefix + template

    def get_rendered_header(self):
        template = Template(self._prepend_template_prefix(self.header))
        return template.render(context=Context(self.format_values))

    def get_rendered_body(self):
        template = Template(self._prepend_template_prefix(self.body))
        return template.render(context=Context(self.format_values))


BUILD_MESSAGES = [
    Message(
        id=BuildAppError.GENERIC_WITH_BUILD_ID,
        header=_("Unknown problem"),
        # Note the message receives the instance it's attached to
        # and could be use it to inject related data
        body=_(
            textwrap.dedent(
                """
                There was a problem with Read the Docs while building your documentation.
                Please try again later.
                If this problem persists,
                report this error to us with your build id ({{instance.pk}}).
                """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildAppError.UPLOAD_FAILED,
        header=_("There was a problem while updating your documentation"),
        body=_(
            textwrap.dedent(
                """
                Make sure this project is outputting files to the correct directory, or try again later.
                If this problem persists, report this error to us with your build id ({{ instance.pk }}).
                """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildAppError.BUILD_TERMINATED_DUE_INACTIVITY,
        header=_("Build terminated due to inactivity"),
        body=_(
            textwrap.dedent(
                """
            This build was terminated due to inactivity.
            If you continue to encounter this error,
            file a support request and reference this build id ({{instance.pk}}).
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.GENERIC,
        header=_("Unknown problem"),
        body=_(
            textwrap.dedent(
                """
            We encountered a problem with a command while building your project.
            To resolve this error, double check your project configuration and installed
            dependencies are correct and have not changed recently.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildMaxConcurrencyError.LIMIT_REACHED,
        header=_("Maximum concurrency limit reached."),
        body=_(
            textwrap.dedent(
                """
            Your project, organization, or user has reached its maximum number of concurrent builds allowed ({{limit}}).
            This build will automatically retry in 5 minutes.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildCancelled.CANCELLED_BY_USER,
        header=_("Build cancelled manually."),
        body=_(
            textwrap.dedent(
                """
            The user has cancelled this build.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildCancelled.SKIPPED_EXIT_CODE_183,
        header=_("Build skipped."),
        body=_(
            textwrap.dedent(
                """
            This build was skipped because
            one of the commands exited with code 183
            """
            ).strip(),
        ),
        type=INFO,
    ),
    Message(
        id=BuildUserError.BUILD_TIME_OUT,
        header=_("Build terminated due to time out."),
        body=_(
            textwrap.dedent(
                """
            The build was terminated due to time out.
            Read more about <a href="https://docs.readthedocs.io/en/stable/builds.html#build-resources">time and memory limits in our documentation</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_EXCESSIVE_MEMORY,
        header=_("Build terminated due to excessive memory consumption."),
        body=_(
            textwrap.dedent(
                """
            This build was terminated due to excessive memory consumption.
            Read more about <a href="https://docs.readthedocs.io/en/stable/builds.html#build-resources">time and memory limits in our documentation</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.VCS_DEPRECATED,
        header=_("Build used a deprecated VCS is not supported: {{vcs}}."),
        body=_(
            textwrap.dedent(
                """
                {{vcs}} VCS is not supported anymore.
                Read more about this in our blog post <a href="https://about.readthedocs.com/blog/2024/02/drop-support-for-subversion-mercurial-bazaar/">Dropping support for Subversion, Mercurial, and Bazaar</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.SSH_KEY_WITH_WRITE_ACCESS,
        header=_("Build aborted due to SSH key with write access."),
        body=_(
            textwrap.dedent(
                """
                This build has failed because the current deploy key on the repository was created with write permission.
                For protection against abuse we've restricted use of these deploy keys.
                A read-only deploy key will need to be set up <b>before December 1st, 2025</b> to continue building this project.
                Read more about this in our <a href="https://about.readthedocs.com/blog/2025/07/ssh-keys-with-write-access/">blog post</a>.
                """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildAppError.BUILD_DOCKER_UNKNOWN_ERROR,
        header=_("Build terminated due to unknown error."),
        body=_(
            textwrap.dedent(
                """
            This build was terminated due to unknown error: {{message}}
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildAppError.BUILDS_DISABLED,
        header=_("Builds are temporary disabled for this project."),
        body=_(
            textwrap.dedent(
                """
            This is due to excessive usage of our resources.
            Please, contact our support team if you think this is a mistake
            and builds should be re-enabled.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_COMMANDS_WITHOUT_OUTPUT,
        header=_("No HTML content found"),
        body=_(
            textwrap.dedent(
                """
             No content was output to the path "$READTHEDOCS_OUTPUT/html".
             Read more about <a href="https://docs.readthedocs.io/page/build-customization.html#where-to-put-files">where to put your built files</a>.
             """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_IS_NOT_A_DIRECTORY,
        header=_("Build output directory is not a directory"),
        body=_(
            textwrap.dedent(
                """
            Build output directory for format "{{artifact_type}}" is not a directory.
            Make sure you created this directory properly when running <code>build.commands</code>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_HAS_0_FILES,
        header=_("Build output directory doesn't contain any file"),
        body=_(
            textwrap.dedent(
                """
            Build output directory for format "{{artifact_type}}" does not contain any files.
            It seems the build process created the directory but did not save any file to it.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_HAS_MULTIPLE_FILES,
        header=_("Build output directory contains multiple files"),
        body=_(
            textwrap.dedent(
                """
            Build output directory for format "{{artifact_type}}" contains multiple files
            and it is not currently supported.
            Please, remove all the files but the "{{artifact_type}}" you want to upload.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_HTML_NO_INDEX_FILE,
        header=_("Index file is not present in HTML output directory"),
        body=_(
            textwrap.dedent(
                """
            Your documentation did not generate an <code>index.html</code> at its root directory.
            This is required for documentation serving at the root URL for this version.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_OLD_DIRECTORY_USED,
        header=_("Your project is outputing files in an old directory"),
        body=_(
            textwrap.dedent(
                """
            Some files were detected in an unsupported output path: <code>_build/html</code>.
            Ensure your project is configured to use the output path
            <code>$READTHEDOCS_OUTPUT/html</code> instead.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.NO_CONFIG_FILE_DEPRECATED,
        header=_("Your project doesn't have a <code>.readthedocs.yaml</code> file"),
        body=_(
            textwrap.dedent(
                """
            The configuration file required to build documentation is missing from your project.
            Add a configuration file to your project to make it build successfully.
            Read more in our <a href="https://docs.readthedocs.io/en/stable/config-file/v2.html">configuration file documentation</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_IMAGE_CONFIG_KEY_DEPRECATED,
        header=_("Configuration key <code>build.image</code> is deprecated"),
        body=_(
            textwrap.dedent(
                """
            The configuration key <code>build.image</code> is deprecated.
            Use <code>build.os</code> instead to continue building your project.
            Read more in our <a href="https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os">configuration file documentation</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OS_REQUIRED,
        header=_("Configuration key <code>build.os</code> is required"),
        body=_(
            textwrap.dedent(
                """
            The configuration key <code>build.os</code> is required to build your documentation.
            Read more in our <a href="https://docs.readthedocs.io/en/stable/config-file/v2.html#build-os">configuration file documentation</a>.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    # TODO: consider exposing the name of the file exceeding the size limit.
    Message(
        id=BuildUserError.FILE_TOO_LARGE,
        header=_("There is at least one file that exceeds the size limit"),
        body=_(
            textwrap.dedent(
                """
            A file from your build process is too large to be processed by Read the Docs.
            Please ensure no generated files are larger than 1GB.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_OUTPUT_HAS_NO_PDF_FILES,
        header=_("There is no PDF file in output directory"),
        body=_(
            textwrap.dedent(
                f"""
             PDF file was not generated/found in "{BUILD_COMMANDS_OUTPUT_PATH_HTML}/pdf" output directory.
             Make sure the PDF file is saved in this directory.
             """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=BuildUserError.BUILD_COMMANDS_IN_BETA,
        header=_("Config key <code>build.commands</code> is in beta"),
        body=_(
            textwrap.dedent(
                """
            <strong>The <code>build.commands</code> feature is in beta, and could have backwards incompatible changes while in beta.</strong>
            Read more at <a href="https://docs.readthedocs.io/page/build-customization.html#override-the-build-process">our documentation</a> to find out its limitations and potential issues.
            """
            ).strip(),
        ),
        type=INFO,
    ),
    Message(
        id=BuildUserError.TEX_FILE_NOT_FOUND,
        header=_("No TeX files were found"),
        body=_(
            textwrap.dedent(
                """
            Read the Docs could not generate a PDF file because the intermediate step generating the TeX file failed.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
]

BUILD_MKDOCS_MESSAGES = [
    Message(
        id=MkDocsYAMLParseError.GENERIC_WITH_PARSE_EXCEPTION,
        header=_(""),
        body=_(
            textwrap.dedent(
                """
            Problem parsing MkDocs YAML configuration. {{exception}}
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.INVALID_DOCS_DIR_CONFIG,
        header=_("MkDocs <code>docs_dir</code> configuration option is invalid"),
        body=_(
            textwrap.dedent(
                """
            The <code>docs_dir</code> option from your <code>mkdocs.yml</code> configuration file has to be a
            string with relative or absolute path.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.INVALID_DOCS_DIR_PATH,
        header=_("MkDocs <code>docs_dir</code> path not found"),
        body=_(
            textwrap.dedent(
                """
                The path specified by <code>docs_dir</code> in the <code>mkdocs.yml</code> file does not exist.
                Make sure this path is correct.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.INVALID_EXTRA_CONFIG,
        header=_("MkDocs <code>{{extra_config}}</code> configuration option is invalid"),
        body=_(
            textwrap.dedent(
                """
            The <code>{{extra_config}}</code> option from your <code>mkdocs.yml</code> configuration file has to be a
            list of relative paths.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.EMPTY_CONFIG,
        header=_("MkDocs configuration file is empty"),
        body=_(
            textwrap.dedent(
                """
            Please make sure the <code>mkdocs.yml</code> configuration file is not empty.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.NOT_FOUND,
        header=_("MkDocs configuration file not found"),
        body=_(
            textwrap.dedent(
                """
            The configuration file for MkDocs was not found.
            Make sure the <code>mkdocs.configuration</code> option is correct,
            and you have the <code>mkdocs.yml</code> in that location.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.CONFIG_NOT_DICT,
        header=_("Unknown error when loading your MkDocs configuration file"),
        body=_(
            textwrap.dedent(
                """
            Your <code>mkdocs.yml</code> configuration file is incorrect.
            Please follow the <a href="https://www.mkdocs.org/user-guide/configuration/">official user guide</a>
            to configure the file properly.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=MkDocsYAMLParseError.SYNTAX_ERROR,
        header=_("Syntax error in <code>mkdocs.yml</code>"),
        body=_(
            textwrap.dedent(
                """
            Your <code>mkdocs.yml</code> could not be loaded,
            possibly due to a syntax error.
            """
            ).strip(),
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
                raise ValueError("A message should be instance of Message or a list of Messages.")

            messages = [messages]

        for message in messages:
            if message.id in messages:
                raise ValueError("A message with the same 'id' is already registered.")
            self.messages[message.id] = message

    def get(self, message_id, format_values=None):
        # Copy to avoid setting format values on the static instance of the
        # message inside the registry, set on a per-request instance instead.
        message = copy.copy(self.messages.get(message_id))

        if message is not None:
            # Always include global variables, override with provided values
            all_format_values = readthedocs_processor(None)
            all_format_values.update(format_values or {})
            message.set_format_values(all_format_values)

        return message


registry = MessagesRegistry()
registry.add(BUILD_MKDOCS_MESSAGES)
registry.add(BUILD_MESSAGES)
