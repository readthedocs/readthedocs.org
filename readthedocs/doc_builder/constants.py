# -*- coding: utf-8 -*-

"""Doc build constants."""

import logging
import os
import re

from django.conf import settings


log = logging.getLogger(__name__)

MKDOCS_TEMPLATE_DIR = os.path.join(
    settings.SITE_ROOT,
    'readthedocs',
    'templates',
    'mkdocs',
)

PDF_RE = re.compile('Output written on (.*?)')

# Docker
DOCKER_SOCKET = settings.DOCKER_SOCKET
DOCKER_VERSION = settings.DOCKER_VERSION
DOCKER_IMAGE = settings.DOCKER_IMAGE
DOCKER_IMAGE_SETTINGS = settings.DOCKER_IMAGE_SETTINGS

old_config = settings.DOCKER_BUILD_IMAGES
if old_config:
    log.warning(
        'Old config detected, DOCKER_BUILD_IMAGES->DOCKER_IMAGE_SETTINGS',
    )
    DOCKER_IMAGE_SETTINGS.update(old_config)

DOCKER_LIMITS = {'memory': '200m', 'time': 600}
DOCKER_LIMITS.update(settings.DOCKER_LIMITS)

DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64
