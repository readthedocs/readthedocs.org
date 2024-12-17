"""Build configuration for rtd."""

import copy
import os
from contextlib import contextmanager
from functools import lru_cache

from django.conf import settings
from pydantic import BaseModel, ValidationError

from readthedocs.config.models import BuildConfig as BuildConfigModel
from readthedocs.core.utils.filesystem import safe_open
from readthedocs.projects.constants import GENERIC

from .exceptions import ConfigError, ConfigValidationError
from .find import find_one
from .models import PythonInstall
from .parser import ParseError, parse
from .validation import validate_dict, validate_path

__all__ = (
    "ALL",
    "load",
    "BuildConfigV2",
    "PIP",
    "SETUPTOOLS",
    "LATEST_CONFIGURATION_VERSION",
)

ALL = "all"
PIP = "pip"
SETUPTOOLS = "setuptools"
CONFIG_FILENAME_REGEX = r"^\.?readthedocs.ya?ml$"

LATEST_CONFIGURATION_VERSION = 2


class BuildConfigBase:

    """
    Config that handles the build of one particular documentation.

    .. note::

       You need to call ``validate`` before the config is ready to use.

    :param raw_config: A dict with all configuration without validation.
    :param source_file: The file that contains the configuration.
                        All paths are relative to this file.
                        If a dir is given, the configuration was loaded
                        from another source (like the web admin).
    """

    PUBLIC_ATTRIBUTES = [
        "version",
        "formats",
        "python",
        "conda",
        "build",
        "doctype",
        "sphinx",
        "mkdocs",
        "submodules",
        "search",
    ]

    version = None

    def __init__(self, raw_config, source_file, base_path=None):
        self._raw_config = copy.deepcopy(raw_config)
        self.source_config = copy.deepcopy(raw_config)
        self.source_file = source_file
        # Support explicit base_path as well as implicit base_path from config_file.
        if base_path:
            self.base_path = base_path
        else:
            if os.path.isdir(self.source_file):
                self.base_path = self.source_file
            else:
                self.base_path = os.path.dirname(self.source_file)

        self._config = {}
        self._build_config = None

    @contextmanager
    def catch_validation_error(self, key=None):
        """Catch a ``ConfigValidationError`` and raises a ``ConfigError`` error."""
        # NOTE: I don't like too much this pattern of re-raising an exception via a context manager.
        # I think we should raise the exception where it happens, instead of encapsulating all of them.
        # The only small limitation that I found is the requirement of passing ``key`` down to where
        # the exception happens.
        # I'm keeping this pattern for now until we decide to refactor it.
        try:
            yield
        except ConfigValidationError as error:
            # Expand the format values defined when the exception is risen
            # with extra ones we have here
            format_values = getattr(error, "format_values", {})
            format_values.update(
                {
                    "key": key if key else error.format_values.get("key"),
                    "value": error.format_values.get("value"),
                    "source_file": os.path.relpath(self.source_file, self.base_path),
                }
            )

            raise ConfigError(
                message_id=error.message_id,
                format_values=format_values,
            ) from error

    def pop(self, name, container, default, raise_ex):
        """
        Search and pop a key inside a dict.

        This will pop the keys recursively if the container is empty.

        :param name: the key name in a list form (``['key', 'inner']``)
        :param container: a dictionary that contains the key
        :param default: default value to return if the key doesn't exists
        :param raise_ex: if True, raises an exception when a key is not found
        """
        key = name[0]
        validate_dict(container)
        if key in container:
            if len(name) > 1:
                value = self.pop(name[1:], container[key], default, raise_ex)
                if not container[key]:
                    container.pop(key)
            else:
                value = container.pop(key)
            return value
        if raise_ex:
            raise ConfigValidationError(
                message_id=ConfigValidationError.VALUE_NOT_FOUND,
                format_values={
                    "value": key,
                },
            )
        return default

    def pop_config(self, key, default=None, raise_ex=False):
        """
        Search and pop a key (recursively) from `self._raw_config`.

        :param key: the key name in a dotted form (``key.innerkey``)
        :param default: Optionally, it can receive a default value
        :param raise_ex: If True, raises an exception when the key is not found
        """
        return self.pop(key.split("."), self._raw_config, default, raise_ex)

    def validate(self):
        raise NotImplementedError()

    @property
    def is_using_conda(self):
        return self._build_config.is_using_conda

    @property
    def is_using_build_commands(self):
        return self._build_config.build.commands is not None

    @property
    def is_using_setup_py_install(self):
        """Check if this project is using `setup.py install` as installation method."""
        for install in self.python.install:
            if isinstance(install, PythonInstall) and install.method == SETUPTOOLS:
                return True
        return False

    @property
    def python_interpreter(self):
        return self._build_config.python_interpreter

    @property
    def docker_image(self):
        return self.settings["os"][self.build.os]

    def as_dict(self):
        config = {}
        for name in self.PUBLIC_ATTRIBUTES:
            attr = getattr(self, name)
            config[name] = attr.model_dump() if isinstance(attr, BaseModel) else attr
        return config

    def __getattr__(self, name):
        """Raise an error for unknown attributes."""
        raise ConfigError(
            message_id=ConfigError.KEY_NOT_SUPPORTED_IN_VERSION,
            format_values={"key": name},
        )


class BuildConfigV2(BuildConfigBase):

    """Version 2 of the configuration file."""

    version = "2"
    valid_formats = ["htmlzip", "pdf", "epub"]
    valid_install_method = [PIP, SETUPTOOLS]
    valid_sphinx_builders = {
        "html": "sphinx",
        "htmldir": "sphinx_htmldir",
        "dirhtml": "sphinx_htmldir",
        "singlehtml": "sphinx_singlehtml",
    }

    @property
    def settings(self):
        return settings.RTD_DOCKER_BUILD_SETTINGS

    def validate(self):
        with self.catch_validation_error():
            try:
                self._build_config = BuildConfigModel(**self._raw_config)
            except ValidationError as exc:
                raise self._cast_pydantic_error(exc.errors()[0])

        # Normalize paths.
        if self._build_config.conda:
            self._build_config.conda.environment = validate_path(self._build_config.conda.environment, self.base_path)
        if self._build_config.python:
            for install in self._build_config.python.install:
                if isinstance(install, PythonInstall):
                    install.requirements = validate_path(install.requirements, self.base_path)
                else:
                    install.path = validate_path(install.path, self.base_path)

        if self._build_config.sphinx and self._build_config.sphinx.configuration:
            self._build_config.sphinx.configuration = validate_path(self._build_config.sphinx.configuration, self.base_path)

        if self._build_config.mkdocs and self._build_config.mkdocs.configuration:
            self._build_config.mkdocs.configuration = validate_path(self._build_config.mkdocs.configuration, self.base_path)

    def _cast_pydantic_error(self, error):
        """
        All possible types of errors that can be found at https://docs.pydantic.dev/latest/errors/validation_errors/.
        """
        key = ".".join(str(part) for part in error['loc'])
        message_id = ConfigError.GENERIC
        context = {}
        if error['type'] == 'missing':
            message_id = ConfigValidationError.VALUE_NOT_FOUND
        if error['type'] in ('model_type', 'dict_type'):
            message_id = ConfigValidationError.INVALID_DICT
        if error['type'] == 'extra_forbidden':
            message_id = ConfigError.INVALID_KEY_NAME
        if error['type'] == 'list_type':
            message_id = ConfigValidationError.INVALID_LIST
        if error['type'] == 'enum':
            message_id = ConfigValidationError.INVALID_CHOICE
            context["expected"] = error['ctx']['expected']
        else:
            message_id = ConfigError.GENERIC
            context["message"] = error['msg']
            # TODO: log to sentry as error, so we can implement all possible errors.

        # If there is an error inside formats, the whole key would be something like
        # formats.list[str-enum[Formats]].0, we don't want to show that.
        if key.startswith('formats.'):
            key = 'formats'

        return ConfigValidationError(
            message_id=message_id,
            format_values={
                "key": key,
                **context,
            },
        )

    def validate(self):
        """Validates and process ``raw_config``."""
        return self.validate_with_pydantic()

    @property
    def formats(self):
        return self._build_config.formats

    @property
    def conda(self):
        return self._build_config.conda

    @property
    @lru_cache(maxsize=1)
    def build(self):
        return self._build_config.build

    @property
    def python(self):
        return self._build_config.python

    @property
    def sphinx(self):
        self._build_config.sphinx

    @property
    def mkdocs(self):
        return self._build_config.mkdocs

    @property
    def doctype(self):
        if self._build_config.build.commands is not None:
            return GENERIC

        if self.mkdocs:
            return "mkdocs"
        return self.valid_sphinx_builder[self.sphinx.builder]

    @property
    def submodules(self):
        return self._build_config.submodules

    @property
    def search(self):
        return self._build_config.search


def load(path, readthedocs_yaml_path=None):
    """
    Load a project configuration and the top-most build config for a given path.

    That is usually the root of the project, but will look deeper.
    """
    # Custom non-default config file location
    if readthedocs_yaml_path:
        filename = os.path.join(path, readthedocs_yaml_path)
        if not os.path.exists(filename):
            raise ConfigError(
                message_id=ConfigError.CONFIG_PATH_NOT_FOUND,
                format_values={"directory": os.path.relpath(filename, path)},
            )
    # Default behavior
    else:
        filename = find_one(path, CONFIG_FILENAME_REGEX)
        if not filename:
            raise ConfigError(ConfigError.DEFAULT_PATH_NOT_FOUND)

    # Allow symlinks, but only the ones that resolve inside the base directory.
    with safe_open(
        filename, "r", allow_symlinks=True, base_path=path
    ) as configuration_file:
        try:
            config = parse(configuration_file.read())
        except ParseError as error:
            raise ConfigError(
                message_id=ConfigError.SYNTAX_INVALID,
                format_values={
                    "filename": os.path.relpath(filename, path),
                    "error_message": str(error),
                },
            ) from error

        version = config.get("version", 2)
        if version not in (2, "2"):
            raise ConfigError(message_id=ConfigError.INVALID_VERSION)

        build_config = BuildConfigV2(
            config,
            source_file=filename,
        )

    build_config.validate()
    return build_config
