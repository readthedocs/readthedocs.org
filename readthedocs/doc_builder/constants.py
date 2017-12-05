# -*- coding: utf-8 -*-
"""Doc build constants."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import logging
import os
import re

from django.conf import settings

log = logging.getLogger(__name__)

SPHINX_TEMPLATE_DIR = os.path.join(
    settings.SITE_ROOT,
    'readthedocs',
    'templates',
    'sphinx',
)
MKDOCS_TEMPLATE_DIR = os.path.join(
    settings.SITE_ROOT,
    'readthedocs',
    'templates',
    'mkdocs',
)
SPHINX_STATIC_DIR = os.path.join(SPHINX_TEMPLATE_DIR, '_static')

PDF_RE = re.compile('Output written on (.*?)')

# Docker
DOCKER_SOCKET = getattr(
    settings,
    'DOCKER_SOCKET',
    'unix:///var/run/docker.sock',
)
DOCKER_VERSION = getattr(settings, 'DOCKER_VERSION', 'auto')
DOCKER_IMAGE = getattr(settings, 'DOCKER_IMAGE', 'readthedocs/build:2.0')
DOCKER_IMAGE_SETTINGS = getattr(settings, 'DOCKER_IMAGE_SETTINGS', {})

old_config = getattr(settings, 'DOCKER_BUILD_IMAGES', None)
if old_config:
    log.warning('Old config detected, DOCKER_BUILD_IMAGES->DOCKER_IMAGE_SETTINGS')
    DOCKER_IMAGE_SETTINGS.update(old_config)

DOCKER_LIMITS = {'memory': '200m', 'time': 600}
DOCKER_LIMITS.update(getattr(settings, 'DOCKER_LIMITS', {}))

DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64
