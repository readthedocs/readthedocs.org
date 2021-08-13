# -*- coding: utf-8 -*-

"""Project exceptions."""

from django.conf import settings
from django.utils.translation import ugettext_noop as _

from readthedocs.doc_builder.exceptions import BuildEnvironmentError


class ProjectConfigurationError(BuildEnvironmentError):

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


class RepositoryError(BuildEnvironmentError):

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
        'You can not have two versions with the name latest or stable.',
    )

    FAILED_TO_CHECKOUT = _('Failed to checkout revision: {}')

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
