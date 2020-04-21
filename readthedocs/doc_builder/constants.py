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
# This assumes 1-builder per server
try:
    total_memory = int(subprocess.check_output("free -m | awk '/^Mem:/{print $2}'", shell=True))
except ValueError:
    # On systems without a `free` command it will return a string to int and raise a ValueError
    log.exception('Failed to get memory size. Using defaults docker limits')
    total_memory = 0

if total_memory > 14000:
    DOCKER_LIMITS.update({
        'memory': '13g',
        'time': 2400,
    })
elif total_memory > 8000:
    DOCKER_LIMITS.update({
        'memory': '7g',
        'time': 1800,
    })
elif total_memory > 4000:
    DOCKER_LIMITS.update({
        'memory': '3g',
        'time': 900,
    })
elif total_memory > 2000:
    DOCKER_LIMITS.update({
        'memory': '1g',
        'time': 600,
    })

if hasattr(settings, 'DOCKER_LIMITS'):
    DOCKER_LIMITS.update(settings.DOCKER_LIMITS)


DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64
