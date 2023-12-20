"""Notifications related to projects."""

from django.utils.translation import gettext_noop as _

from readthedocs.notifications.constants import ERROR, INFO
from readthedocs.notifications.messages import Message, registry
from readthedocs.projects.exceptions import (
    ProjectConfigurationError,
    RepositoryError,
    UserFileNotFound,
)

MESSAGE_PROJECT_SKIP_BUILDS = "project:invalid:skip-builds"
messages = [
    Message(
        id=MESSAGE_PROJECT_SKIP_BUILDS,
        header=_("Build skipped for this project"),
        body=_(
            """
            Your project is currently disabled for abuse of the system.
            Please make sure it isn't using unreasonable amounts of resources or triggering lots of builds in a short amount of time.
            Please <a href="mailto:{SUPPORT_EMAIL}">contact support</a> to get your project re-enabled.
            """
        ),
        type=INFO,
    ),
    Message(
        id=RepositoryError.GENERIC,
        header=_("Error when cloning the repository"),
        body=_(
            """
            There was a problem cloning your repository.
            Please check the command output for more information.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.DUPLICATED_RESERVED_VERSIONS,
        header=_("Duplicated reserved versions"),
        body=_(
            """
            You can not have two versions with the name latest or stable.
            Ensure you don't have both a branch and a tag with this name.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.FAILED_TO_CHECKOUT,
        header=_("Error when checking out the repository"),
        body=_(
            """
            Failed to checkout revision: <code>{revision}</code>
            """
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_ALLOWED,
        header=_("Error when cloning the repository"),
        body=_(
            """
            There was a problem connecting to your repository,
            ensure that your repository URL is correct.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=RepositoryError.CLONE_ERROR_WITH_PRIVATE_REPO_NOT_ALLOWED,
        header=_("Error when cloning the repository"),
        body=_(
            """
            There was a problem connecting to your repository,
            ensure that your repository URL is correct and your repository is public.
            Private repositories are not supported.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ProjectConfigurationError.NOT_FOUND,
        header=_("Sphinx's configuration file missing"),
        body=_(
            """
            A configuration file was not found.
            Make sure you have a <code>conf.py</code> file in your repository.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=ProjectConfigurationError.MULTIPLE_CONF_FILES,
        header=_("Multiple Sphinx's configuration file found"),
        body=_(
            """
            We found more than one <code>conf.py</code> and are not sure which one to use.
            Please, specify the correct file under the Advanced settings tab
            in the project's Admin.
            """
        ),
        type=ERROR,
    ),
    Message(
        id=UserFileNotFound.FILE_NOT_FOUND,
        header=_("Expected file not found"),
        body=_(
            """
            The file <code>{filename}</code> doesn't exist. Make sure it's a valid file path.
            """
        ),
        type=ERROR,
    ),
]
registry.add(messages)
