# -*- coding: utf-8 -*-

"""Doc build constants."""

import logging
import re

from django.conf import settings


log = logging.getLogger(__name__)

PDF_RE = re.compile('Output written on (.*?)')

# Docker
DOCKER_SOCKET = settings.DOCKER_SOCKET
DOCKER_VERSION = settings.DOCKER_VERSION
DOCKER_IMAGE = settings.DOCKER_IMAGE
DOCKER_IMAGE_SETTINGS = settings.DOCKER_IMAGE_SETTINGS
DOCKER_LIMITS = settings.DOCKER_LIMITS

old_config = settings.DOCKER_BUILD_IMAGES
if old_config:
    log.warning(
        'Old config detected, DOCKER_BUILD_IMAGES->DOCKER_IMAGE_SETTINGS',
    )
    DOCKER_IMAGE_SETTINGS.update(old_config)

DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64
