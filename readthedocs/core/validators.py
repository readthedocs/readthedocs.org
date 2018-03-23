"""Validators for core app."""

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

    def __call__(self, value):
        allow_private_repos = getattr(settings, 'ALLOW_PRIVATE_REPOS', False)
        public_schemes = ['https', 'http', 'git', 'ftps', 'ftp']
        private_schemes = ['ssh', 'ssh+git']
        valid_schemes = public_schemes
        if allow_private_repos:
            valid_schemes += private_schemes
        url = urlparse(value)
        if (
                (
                    url.scheme not in valid_schemes and \
                    '@' not in value and \
                    not value.startswith('lp:')
                ) or \
                (
                    value.startswith('/') or \
                    value.startswith('file://') or \
                    value.startswith('.')
                )
        ):
            # Avoid ``/path/to/local/file`` and ``file://`` scheme but allow
            # ``git@github.com:user/project.git`` and ``lp:bazaar``
            raise ValidationError(_('Invalid scheme for URL'))
        elif '&&' in value or '|' in value:
            raise ValidationError(_('Invalid character in the URL'))
        elif (
                ('@' in value or url.scheme in private_schemes) and
                not allow_private_repos
        ):
            raise ValidationError('Clonning via SSH is not supported')
        return value

validate_repository_url = RepositoryURLValidator()
