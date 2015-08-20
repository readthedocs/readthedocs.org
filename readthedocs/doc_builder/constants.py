'''Doc build constants'''

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


DOCKER_SOCKET = getattr(settings, 'DOCKER_SOCKET', 'unix:///var/run/docker.sock')
DOCKER_VERSION = getattr(settings, 'DOCKER_VERSION', 'auto')
DOCKER_IMAGE = getattr(settings, 'DOCKER_IMAGE', 'rtfd-build')
DOCKER_LIMITS = {'memory': '200m', 'time': 600}
DOCKER_LIMITS.update(getattr(settings, 'DOCKER_LIMITS', {}))

DOCKER_TIMEOUT_EXIT_CODE = 42
DOCKER_OOM_EXIT_CODE = 137
