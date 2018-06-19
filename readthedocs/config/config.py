from contextlib import contextmanager
import re
import os

from .find import find_one
from .parser import ParseError
from .parser import parse
from .validation import (ValidationError, validate_bool, validate_choice,
                         validate_directory, validate_file, validate_list,
                         validate_string)


__all__ = (
    'load', 'BuildConfig', 'ConfigError', 'InvalidConfig', 'ProjectConfig')


CONFIG_FILENAMES = ()


BASE_INVALID = ''
BASE_NOT_A_DIR = ''
CONFIG_SYNTAX_INVALID = ''
CONFIG_REQUIRED = ''
NAME_REQUIRED = ''
NAME_INVALID = ''
CONF_FILE_REQUIRED = ''
TYPE_REQUIRED = ''
PYTHON_INVALID = ''

DOCKER_DEFAULT_IMAGE = ''
DOCKER_DEFAULT_VERSION = ''
# These map to coordisponding settings in the .org,
# so they haven't been renamed.
DOCKER_IMAGE = '{}:{}'.format(DOCKER_DEFAULT_IMAGE, DOCKER_DEFAULT_VERSION)
DOCKER_IMAGE_SETTINGS = {}


class ConfigError(Exception):

    def __init__(self, message, code):
        self.code = code
        super(ConfigError, self).__init__(message)


class InvalidConfig(ConfigError):
    pass


class BuildConfig(dict):
    pass


class ProjectConfig(list):
    pass


def load(path, env_config):
    pass

