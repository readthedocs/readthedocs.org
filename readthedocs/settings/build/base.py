# pylint: disable=missing-docstring

import sys


class CommunityBuildSettingsMixin:

    read_only_settings = ['DATABASES', 'DONT_HIT_DB']

    DONT_HIT_DB = True

    DOCKER_ENABLE = True
