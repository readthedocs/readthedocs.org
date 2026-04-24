"""Doc build constants."""

import re

import structlog
from django.conf import settings


log = structlog.get_logger(__name__)

PDF_RE = re.compile("Output written on (.*?)")

# Docker
DOCKER_SOCKET = settings.DOCKER_SOCKET
DOCKER_VERSION = settings.DOCKER_VERSION
DOCKER_IMAGE = settings.DOCKER_IMAGE
DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64

# Why 183 exit code?
#
# >>> sum(list('skip'.encode('ascii')))
# 439
# >>> 439 % 256
# 183
RTD_SKIP_BUILD_EXIT_CODE = 183
