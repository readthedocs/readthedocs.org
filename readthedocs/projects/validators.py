"""Validators for projects app."""

import re
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class DomainNameValidator(RegexValidator):
    message = _('Enter a valid plain or internationalized domain name value')
    # Based on the domain name pattern from https://api.cloudflare.com/#zone-list-zones.
    regex = re.compile(
        r'^([a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9-]{2,20}$'
    )


validate_domain_name = DomainNameValidator()


@deconstructible
class NoIPValidator(RegexValidator):
    message = _("The domain name can't be an IP address.")
    regex = re.compile(r"^(\d+\.)+\d+$")
    inverse_match = True


validate_no_ip = NoIPValidator()


@deconstructible
class RepositoryURLValidator:

    disallow_relative_url = True

    # Pattern for ``git@github.com:user/repo`` pattern
    re_git_user = re.compile(r'^[\w]+@.+')

    def __call__(self, value):
        public_schemes = ['https', 'http', 'git', 'ftps', 'ftp']
        private_schemes = ['ssh', 'ssh+git']
        local_schemes = ['file']
        valid_schemes = public_schemes
        if settings.ALLOW_PRIVATE_REPOS:
            valid_schemes += private_schemes
        if settings.DEBUG:  # allow `file://` urls in dev
            valid_schemes += local_schemes
        url = urlparse(value)

        # Malicious characters go first
        if '&&' in value or '|' in value:
            raise ValidationError(_('Invalid character in the URL'))
        if url.scheme in valid_schemes:
            return value

        # Repo URL is not a supported scheme at this point, but there are
        # several cases where we might support it
        # Launchpad
        if value.startswith('lp:'):
            return value
        # Relative paths are conditionally supported
        if value.startswith('.') and not self.disallow_relative_url:
            return value
        # SSH cloning and ``git@github.com:user/project.git``
        if self.re_git_user.search(value) or url.scheme in private_schemes:
            if settings.ALLOW_PRIVATE_REPOS:
                return value

            # Throw a more helpful error message
            raise ValidationError('Manual cloning via SSH is not supported')

        # No more valid URLs without supported URL schemes
        raise ValidationError(_('Invalid scheme for URL'))


class SubmoduleURLValidator(RepositoryURLValidator):

    """
    A URL validator for repository submodules.

    If a repository has a relative submodule, the URL path is effectively the
    supermodule's remote ``origin`` URL with the relative path applied.

    From the git docs::

        ``<repository>`` is the URL of the new submodule's origin repository.
        This may be either an absolute URL, or (if it begins with ``./`` or
        ``../``), the location relative to the superproject's default remote
        repository
    """

    disallow_relative_url = False


validate_repository_url = RepositoryURLValidator()
validate_submodule_url = SubmoduleURLValidator()


def validate_custom_prefix(project, prefix):
    """
    Validate and clean the custom path prefix for a project.

    We validate that the prefix is defined in the correct project.
    Prefixes must be defined in the main project if the project is a translation.

    Raises ``ValidationError`` if the prefix is invalid.

    :param project: Project to validate the prefix
    :param prefix: Prefix to validate
    """
    if not prefix:
        return

    if project.main_language_project:
        raise ValidationError(
            "This project is a translation of another project, "
            "the custom prefix must be defined in the main project.",
            code="invalid_project",
        )

    return _clean_prefix(prefix)


def validate_custom_subproject_prefix(project, prefix):
    """
    Validate and clean the custom subproject prefix for a project.

    We validate that the subproject prefix is defined in a super project,
    not in a subproject.

    Raises ``ValidationError`` if the prefix is invalid.

    :param project: Project to validate the prefix
    :param prefix: Subproject prefix to validate
    """
    if not prefix:
        return

    main_project = project.main_language_project or project
    if main_project.is_subproject:
        raise ValidationError(
            "This project is a subproject, the subproject prefix must "
            "be defined in the parent project custom_subproject_prefix attribute.",
            code="invalid_project",
        )

    return _clean_prefix(prefix)


def _clean_prefix(prefix):
    """
    Validate and clean a prefix.

    Prefixes must:

    - Start and end with a slash

    :param prefix: Prefix to clean and validate
    """
    # TODO we could validate that only alphanumeric characters are used?
    prefix = prefix.strip("/")
    if not prefix:
        return "/"
    return f"/{prefix}/"
