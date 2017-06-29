"""Doc build constants"""

from __future__ import absolute_import
import os
import re

from django.conf import settings


SPHINX_TEMPLATE_DIR = os.path.join(settings.SITE_ROOT, 'readthedocs',
                                   'templates', 'sphinx')
MKDOCS_TEMPLATE_DIR = os.path.join(settings.SITE_ROOT, 'readthedocs',
                                   'templates', 'mkdocs')
SPHINX_STATIC_DIR = os.path.join(SPHINX_TEMPLATE_DIR, '_static')

PDF_RE = re.compile('Output written on (.*?)')

# Docker
DOCKER_SOCKET = getattr(settings, 'DOCKER_SOCKET', 'unix:///var/run/docker.sock')
DOCKER_VERSION = getattr(settings, 'DOCKER_VERSION', 'auto')
DOCKER_IMAGE = getattr(settings, 'DOCKER_IMAGE', 'readthedocs/build:2.0')
DOCKER_LIMITS = {'memory': '200m', 'time': 600}
DOCKER_LIMITS.update(getattr(settings, 'DOCKER_LIMITS', {}))

DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137

DOCKER_HOSTNAME_MAX_LEN = 64

# Build images
BUILD_IMAGES = {
    'readthedocs/build:1.0': {
        'python': {'supported_versions': [2, 2.7, 3, 3.4]},
    },
    'readthedocs/build:2.0': {
        'python': {'supported_versions': [2, 2.7, 3, 3.5]},
    },
    'readthedocs/build:latest': {
        'python': {'supported_versions': [2, 2.7, 3, 3.3, 3.4, 3.5, 3.6]},
    },
}
