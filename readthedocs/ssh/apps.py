# -*- coding: utf-8 -*-
"""App configuration for ssh application."""
from __future__ import division, print_function, unicode_literals

from django.apps import AppConfig
from django.core.checks import Error, register
from django.conf import settings


class SshConfig(AppConfig):

    """SSH App configuration."""

    name = 'readthedocs.ssh'
    verbose_name = 'SSH Keys'


@register()
def check_valid_encryption_key(app_configs, **kwargs):
    from encrypted_model_fields.fields import parse_key

    errors = []
    keys = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
    if not keys:
        errors.append(
            Error(
                'FIELD_ENCRYPTION_KEY must be defined in settings',
                hint='Use the "generate_encryption_key" management command to generate a valid one ',  # noqa
                id='ssh.E001',
            ),
        )
    else:
        default_key = 'P98DEYWoSuLmgXdRGzJkbo1JWeiHf4ghpFI8QvV3hRI='
        if not isinstance(keys, (tuple, list)):
            keys = [keys]

        for key in keys:
            try:
                parse_key(key)
            except Exception:
                errors.append(
                    Error(
                        'FIELD_ENCRYPTION_KEY setting has an incorrect padding',
                        hint='Use the "generate_encryption_key" management command to generate a valid one ',  # noqa
                        id='ssh.E002',
                    ),
                )

            # Check against the default value to prevent users to run the
            # instance in production with a shared encryption key
            if key == default_key and not settings.DEBUG:
                errors.append(
                    Error(
                        'You are using the default value for FIELD_ENCRYPTION_KEY',
                        hint='Change it by running the "generate_encryption_key" management command',
                        id='ssh.E003',
                    ),
                )

    return errors
