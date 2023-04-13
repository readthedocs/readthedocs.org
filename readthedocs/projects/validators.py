"""Validators for projects app."""

import re
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.safestring import mark_safe
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


def validate_build_config_file(path):
    """
    Validate that user input is a good relative repository path.

    By 'good', we mean that it's a valid unix path,
    but not all valid unix paths are good repository paths.

    This validator checks for common mistakes.
    """
    invalid_characters = "[]{}()`'\"\\%&<>|,"
    valid_filenames = [".readthedocs.yaml"]

    if path.startswith("/"):
        raise ValidationError(
            _(
                "Use a relative path. It should not begin with '/'. "
                "The path is relative to the root of your repository."
            ),
            code="path_invalid",
        )
    if path.endswith("/"):
        raise ValidationError(
            _("The path cannot end with '/', as it cannot be a directory."),
            code="path_invalid",
        )
    if ".." in path:
        raise ValidationError(
            _("Found invalid sequence in path: '..'"),
            code="path_invalid",
        )
    if any(ch in path for ch in invalid_characters):
        raise ValidationError(
            mark_safe(
                _(
                    "Found invalid character. Avoid these characters: "
                    "<code>{invalid_characters}</code>"
                ).format(invalid_characters=invalid_characters),
            ),
            code="path_invalid",
        )

    is_valid = any(fn == path for fn in valid_filenames) or any(
        path.endswith(f"/{fn}") for fn in valid_filenames
    )
    if not is_valid and len(valid_filenames) == 1:
        raise ValidationError(
            mark_safe(
                _("The only allowed filename is <code>{filename}</code>.").format(
                    filename=valid_filenames[0]
                ),
            ),
            code="path_invalid",
        )
    if not is_valid:
        raise ValidationError(
            mark_safe(
                _("The only allowed filenames are <code>{filenames}</code>.").format(
                    filenames=", ".join(valid_filenames)
                ),
            ),
            code="path_invalid",
        )
