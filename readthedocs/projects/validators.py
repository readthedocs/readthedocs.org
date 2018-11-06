"""Validators for projects app."""

# From https://github.com/django/django/pull/3477/files
from __future__ import absolute_import
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from future.backports.urllib.parse import urlparse


domain_regex = (
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}(?<!-)\.?)|'
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
)


@deconstructible
class DomainNameValidator(RegexValidator):
    message = _('Enter a valid plain or internationalized domain name value')
    regex = re.compile(domain_regex, re.IGNORECASE)

    def __init__(self, accept_idna=True, **kwargs):
        message = kwargs.get('message')
        self.accept_idna = accept_idna
        super(DomainNameValidator, self).__init__(**kwargs)
        if not self.accept_idna and message is None:
            self.message = _('Enter a valid domain name value')

    def __call__(self, value):
        try:
            super(DomainNameValidator, self).__call__(value)
        except ValidationError as exc:
            if not self.accept_idna:
                raise
            if not value:
                raise
            try:
                idnavalue = value.encode('idna')
            except UnicodeError:
                raise exc
            super(DomainNameValidator, self).__call__(idnavalue)


validate_domain_name = DomainNameValidator()


@deconstructible
class RepositoryURLValidator(object):

    disallow_relative_url = True

    # Pattern for ``git@github.com:user/repo`` pattern
    re_git_user = re.compile(r'^[\w]+@.+')

    def __call__(self, value):
        allow_private_repos = getattr(settings, 'ALLOW_PRIVATE_REPOS', False)
        public_schemes = ['https', 'http', 'git', 'ftps', 'ftp']
        private_schemes = ['ssh', 'ssh+git']
        local_schemes = ['file']
        valid_schemes = public_schemes
        if allow_private_repos:
            valid_schemes += private_schemes
        if getattr(settings, 'DEBUG'):  # allow `file://` urls in dev
            valid_schemes += local_schemes
        url = urlparse(value)

        # Malicious characters go first
        if '&&' in value or '|' in value:
            raise ValidationError(_('Invalid character in the URL'))
        elif url.scheme in valid_schemes:
            return value

        # Repo URL is not a supported scheme at this point, but there are
        # several cases where we might support it
        # Launchpad
        elif value.startswith('lp:'):
            return value
        # Relative paths are conditionally supported
        elif value.startswith('.') and not self.disallow_relative_url:
            return value
        # SSH cloning and ``git@github.com:user/project.git``
        elif self.re_git_user.search(value) or url.scheme in private_schemes:
            if allow_private_repos:
                return value

            # Throw a more helpful error message
            raise ValidationError('Manual cloning via SSH is not supported')

        # No more valid URLs without supported URL schemes
        raise ValidationError(_('Invalid scheme for URL'))


class SubmoduleURLValidator(RepositoryURLValidator):

    """
    A URL validator for repository submodules

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
