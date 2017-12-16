"""Project exceptions."""

from django.conf import settings
from django.utils.translation import ugettext_noop as _

from readthedocs.doc_builder.exceptions import BuildEnvironmentError


class ProjectConfigurationError(BuildEnvironmentError):

    """Error raised trying to configure a project for build."""

    NOT_FOUND = _(
        'A configuration file was not found. '
        'Make sure you have a conf.py file in your repository.'
    )


class RepositoryError(BuildEnvironmentError):

    """Failure during repository operation."""

    PRIVATE_ALLOWED = _(
        'There was a problem connecting to your repository, '
        'ensure that your repository URL is correct.'
    )
    PRIVATE_NOT_ALLOWED = _(
        'There was a problem connecting to your repository, '
        'ensure that your repository URL is correct and your repository is public. '
        'Private repositories are not supported.'
    )

    def get_default_message(self):
        if settings.ALLOW_PRIVATE_REPOS:
            return self.PRIVATE_ALLOWED
        return self.PRIVATE_NOT_ALLOWED


class ProjectSpamError(Exception):

    """
    Error raised when a project field has detected spam.

    This error is not raised to users, we use this for banning users in the
    background.
    """

    pass
