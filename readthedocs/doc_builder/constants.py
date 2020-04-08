# -*- coding: utf-8 -*-

"""Doc build constants."""

import logging
import re
import subprocess

from django.conf import settings


log = logging.getLogger(__name__)

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

DOCKER_LIMITS = {
    'memory': '200m',
    'time': 600,
}

# Set docker limits dynamically based on system memory
free_memory = int(subprocess.check_output("free -m | awk '/^Mem:/{print $2}'", shell=True))
if free_memory > 14000:
    DOCKER_LIMITS.update({
        'memory': '13g',
        'time': 2400,
    })
elif free_memory > 8000:
    DOCKER_LIMITS.update({
        'memory': '7g',
        'time': 1800,
    })
elif free_memory > 4000:
    DOCKER_LIMITS.update({
        'memory': '3g',
        'time': 900,
    })
elif free_memory > 2000:
    DOCKER_LIMITS.update({
        'memory': '1g',
        'time': 600,
    })

DOCKER_LIMITS.update(settings.DOCKER_LIMITS)


DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64
