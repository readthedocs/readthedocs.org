
"""Project exceptions."""

from django.conf import settings
from django.utils.translation import gettext_noop as _

from readthedocs.doc_builder.exceptions import BuildAppError, BuildUserError


class ProjectConfigurationError(BuildUserError):

    """Error raised trying to configure a project for build."""

    NOT_FOUND = _(
        'A configuration file was not found. '
        'Make sure you have a conf.py file in your repository.',
    )

    MULTIPLE_CONF_FILES = _(
        'We found more than one conf.py and are not sure which one to use. '
        'Please, specify the correct file under the Advanced settings tab '
        "in the project's Admin.",
    )


class RepositoryError(BuildUserError):

    """Failure during repository operation."""

    PRIVATE_ALLOWED = _(
        'There was a problem connecting to your repository, '
        'ensure that your repository URL is correct.',
    )
    PRIVATE_NOT_ALLOWED = _(
        'There was a problem connecting to your repository, '
        'ensure that your repository URL is correct and your repository is public. '
        'Private repositories are not supported.',
    )
    INVALID_SUBMODULES = _(
        'One or more submodule URLs are not valid: {}, '
        'git/ssh URL schemas for submodules are not supported.'
    )
    DUPLICATED_RESERVED_VERSIONS = _(
        "You can not have two versions with the name latest or stable."
        " Ensure you don't have both a branch and a tag with this name."
    )

    FAILED_TO_CHECKOUT = _('Failed to checkout revision: {}')

    GENERIC_ERROR = _(
        "There was a problem cloning your repository. "
        "Please check the command output for more information.",
    )

    # NOTE: we are not using `@property` here because Python 3.8 does not
    # suport `@property` together with `@classmethod`. On Python >= 3.9, we
    # could call `RepositoryError.CLONE_ERROR` without parenthesis and it will
    # work. However, for now, we are just using a class method and calling it
    # as a function/method.
    @classmethod
    def CLONE_ERROR(cls):  # noqa: N802
        if settings.ALLOW_PRIVATE_REPOS:
            return cls.PRIVATE_ALLOWED
        return cls.PRIVATE_NOT_ALLOWED

    def get_default_message(self):
        return self.GENERIC_ERROR


class SyncRepositoryLocked(BuildAppError):

    """Error risen when there is another sync_repository_task already running."""
