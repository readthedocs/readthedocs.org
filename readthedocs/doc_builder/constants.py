# -*- coding: utf-8 -*-

"""Doc build constants."""

import logging
import re

from django.conf import settings


log = logging.getLogger(__name__)

PDF_RE = re.compile('Output written on (.*?)')

# Docker
RTD_DOCKER_SOCKET = settings.RTD_DOCKER_SOCKET
RTD_DOCKER_VERSION = settings.RTD_DOCKER_VERSION
RTD_DOCKER_IMAGE = settings.RTD_DOCKER_IMAGE
RTD_DOCKER_IMAGE_SETTINGS = settings.RTD_DOCKER_IMAGE_SETTINGS

old_config = settings.RTD_DOCKER_BUILD_IMAGES
if old_config:
    log.warning(
        'Old config detected, DOCKER_BUILD_IMAGES->DOCKER_IMAGE_SETTINGS',
    )
    RTD_DOCKER_IMAGE_SETTINGS.update(old_config)

RTD_DOCKER_LIMITS = {'memory': '200m', 'time': 600}
RTD_DOCKER_LIMITS.update(settings.RTD_DOCKER_LIMITS)

DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64
