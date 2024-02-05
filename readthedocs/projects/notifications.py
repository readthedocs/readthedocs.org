"""Notifications related to projects."""
import textwrap

from django.utils.translation import gettext_noop as _

from readthedocs.notifications.constants import ERROR, INFO, WARNING
from readthedocs.notifications.messages import Message, registry
from readthedocs.projects.exceptions import (
    ProjectAutomaticCreationDisallowed,
    ProjectConfigurationError,
    ProjectManualCreationDisallowed,
    RepositoryError,
    SyncRepositoryLocked,
    UserFileNotFound,
)

MESSAGE_PROJECT_SKIP_BUILDS = "project:invalid:skip-builds"
messages = [
    Message(
        id=MESSAGE_PROJECT_SKIP_BUILDS,
        header=_("Build skipped for this project"),
        body=_(
            textwrap.dedent(
                """
            Your project is currently disabled for abuse of the system.
            Please make sure it isn't using unreasonable amounts of resources or triggering lots of builds in a short amount of time.
            Please <a href="mailto:{{SUPPORT_EMAIL}}">contact support</a> to get your project re-enabled.
            """
            ).strip(),
        ),
        type=INFO,
    ),
    Message(
        id=RepositoryError.GENERIC,
        header=_("Error while cloning the repository"),
        body=_(
            textwrap.dedent(
                """
            There was a problem cloning your repository.
            Please check the command output for more information.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.DUPLICATED_RESERVED_VERSIONS,
        header=_("Duplicated reserved versions"),
        body=_(
            textwrap.dedent(
                """
            You can not have two versions with the name latest or stable.
            Ensure you don't have both a branch and a tag with this name.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.FAILED_TO_CHECKOUT,
        header=_("Error while checking out the repository"),
        body=_(
            textwrap.dedent(
                """
            Failed to checkout revision: <code>{{revision}}</code>
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_ALLOWED,
        header=_("Error while cloning the repository"),
        body=_(
            textwrap.dedent(
                """
            There was a problem connecting to your repository,
            ensure that your repository URL is correct.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_NOT_ALLOWED,
        header=_("Error while cloning the repository"),
        body=_(
            textwrap.dedent(
                """
            There was a problem connecting to your repository,
            ensure that your repository URL is correct and your repository is public.
            Private repositories are not supported.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ProjectConfigurationError.NOT_FOUND,
        header=_("Sphinx configuration file is missing"),
        body=_(
            textwrap.dedent(
                """
            A configuration file was not found.
            Make sure you have a <code>conf.py</code> file in your repository.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=ProjectConfigurationError.MULTIPLE_CONF_FILES,
        header=_("Multiple Sphinx configuration files found"),
        body=_(
            textwrap.dedent(
                """
            We found more than one <code>conf.py</code> and are not sure which one to use.
            Please, specify the correct file under the Advanced settings tab
            in the project's Admin.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=UserFileNotFound.FILE_NOT_FOUND,
        header=_("Expected file not found"),
        body=_(
            textwrap.dedent(
                """
            The file <code>{{filename}}</code> doesn't exist. Make sure it's a valid file path.
            """
            ).strip(),
        ),
        type=ERROR,
    ),
    Message(
        id=SyncRepositoryLocked.REPOSITORY_LOCKED,
        header=_("Repository locked"),
        body=_(
            textwrap.dedent(
                """
                We can't perform the versions/branches synchronize at the moment.
                There is another sync already running.
                """
            ).strip(),
        ),
        type=WARNING,
    ),
    # The following messages are added to the registry but are only used
    # directly by the project creation view template. These could be split out
    # directly for use by import, instead of reusing message id lookup.
    Message(
        id=ProjectAutomaticCreationDisallowed.NO_CONNECTED_ACCOUNT,
        header=_("No connected services found"),
        body=_(
            textwrap.dedent(
                # Translators: "connected service" refers to the user setting page for "Connected Services"
                """
                You must first <a href="{{ url }}">add a connected service to your account</a>
                to enable automatic configuration of repositories.
                """
            ).strip(),
        ),
        type=WARNING,
    ),
    Message(
        id=ProjectAutomaticCreationDisallowed.SSO_ENABLED,
        header=_("Organization single sign-on enabled"),
        body=_(
            textwrap.dedent(
                """
                Only organization owners may create new projects when single
                sign-on is enabled.
                """
            ).strip(),
        ),
        type=WARNING,
    ),
    Message(
        id=ProjectManualCreationDisallowed.SSO_ENABLED,
        header=_("Organization single sign-on enabled"),
        body=_(
            textwrap.dedent(
                """
                Projects cannot be manually configured when single sign-on is
                enabled.
                """
            ).strip(),
        ),
        type=WARNING,
    ),
]
registry.add(messages)
