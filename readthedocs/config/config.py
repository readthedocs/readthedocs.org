"""Build configuration for rtd."""
from __future__ import division, print_function, unicode_literals

import os
import re
from contextlib import contextmanager

import six

from .find import find_one
from .parser import ParseError, parse
from .validation import (
    ValidationError, validate_bool, validate_choice, validate_directory,
    validate_file, validate_list, validate_string)

__all__ = (
    'load', 'BuildConfig', 'ConfigError', 'ConfigOptionNotSupportedError',
    'InvalidConfig', 'ProjectConfig'
)


CONFIG_FILENAMES = ('readthedocs.yml', '.readthedocs.yml')


CONFIG_NOT_SUPPORTED = 'config-not-supported'
BASE_INVALID = 'base-invalid'
BASE_NOT_A_DIR = 'base-not-a-directory'
CONFIG_SYNTAX_INVALID = 'config-syntax-invalid'
CONFIG_REQUIRED = 'config-required'
NAME_REQUIRED = 'name-required'
NAME_INVALID = 'name-invalid'
CONF_FILE_REQUIRED = 'conf-file-required'
TYPE_REQUIRED = 'type-required'
PYTHON_INVALID = 'python-invalid'

DOCKER_DEFAULT_IMAGE = 'readthedocs/build'
DOCKER_DEFAULT_VERSION = '2.0'
# These map to coordisponding settings in the .org,
# so they haven't been renamed.
DOCKER_IMAGE = '{}:{}'.format(DOCKER_DEFAULT_IMAGE, DOCKER_DEFAULT_VERSION)
DOCKER_IMAGE_SETTINGS = {
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


class ConfigError(Exception):

    """Base error for the rtd configuration file."""

    def __init__(self, message, code):
        self.code = code
        super(ConfigError, self).__init__(message)


class ConfigOptionNotSupportedError(ConfigError):

    """Error for unsupported configuration options in a version."""

    def __init__(self, configuration):
        self.configuration = configuration
        template = (
            'The "{}" configuration option is not supported in this version'
        )
        super(ConfigOptionNotSupportedError, self).__init__(
            template.format(self.configuration),
            CONFIG_NOT_SUPPORTED
        )


class InvalidConfig(ConfigError):

    """Error for a specific key validation."""

    message_template = 'Invalid "{key}": {error}'

    def __init__(self, key, code, error_message, source_file=None,
                 source_position=None):
        self.key = key
        self.code = code
        self.source_file = source_file
        self.source_position = source_position
        message = self.message_template.format(
            key=key,
            code=code,
            error=error_message)
        super(InvalidConfig, self).__init__(message, code=code)


class BuildConfigBase(object):

    """
    Config that handles the build of one particular documentation.

    You need to call ``validate`` before the config is ready to use.
    Also setting the ``output_base`` is required before using it for a build.
    """

    version = None

    def __init__(self, env_config, raw_config, source_file, source_position):
        self.env_config = env_config
        self.raw_config = raw_config
        self.source_file = source_file
        self.source_position = source_position
        self.defaults = self.env_config.get('defaults', {})

        self._config = {}

    def error(self, key, message, code):
        """Raise an error related to ``key``."""
        source = '{file} [{pos}]'.format(
            file=self.source_file,
            pos=self.source_position
        )
        error_message = '{source}: {message}'.format(
            source=source,
            message=message
        )
        raise InvalidConfig(
            key=key,
            code=code,
            error_message=error_message,
            source_file=self.source_file,
            source_position=self.source_position
        )

    @contextmanager
    def catch_validation_error(self, key):
        """Catch a ``ValidationError`` and raises an ``InvalidConfig`` error."""
        try:
            yield
        except ValidationError as error:
            raise InvalidConfig(
                key=key,
                code=error.code,
                error_message=str(error),
                source_file=self.source_file,
                source_position=self.source_position
            )

    def validate(self):
        raise NotImplementedError()

    @property
    def python_interpreter(self):
        ver = self.python_full_version
        return 'python{0}'.format(ver)

    @property
    def python_full_version(self):
        ver = self.python_version
        if ver in [2, 3]:
            # Get the highest version of the major series version if user only
            # gave us a version of '2', or '3'
            ver = max(
                v
                for v in self.get_valid_python_versions()
                if v < ver + 1
            )
        return ver

    def __getattr__(self, name):
        """Raise an error for unknown attributes."""
        raise ConfigOptionNotSupportedError(name)


class BuildConfig(BuildConfigBase):

    """Version 1 of the configuration file."""

    BASE_INVALID_MESSAGE = 'Invalid value for base: {base}'
    BASE_NOT_A_DIR_MESSAGE = '"base" is not a directory: {base}'
    NAME_REQUIRED_MESSAGE = 'Missing key "name"'
    NAME_INVALID_MESSAGE = (
        'Invalid name "{name}". Valid values must match {name_re}')
    TYPE_REQUIRED_MESSAGE = 'Missing key "type"'
    CONF_FILE_REQUIRED_MESSAGE = 'Missing key "conf_file"'
    PYTHON_INVALID_MESSAGE = '"python" section must be a mapping.'
    PYTHON_EXTRA_REQUIREMENTS_INVALID_MESSAGE = (
        '"python.extra_requirements" section must be a list.')

    PYTHON_SUPPORTED_VERSIONS = [2, 2.7, 3, 3.5]
    DOCKER_SUPPORTED_VERSIONS = ['1.0', '2.0', 'latest']

    version = '1'

    def get_valid_types(self):  # noqa
        """Get all valid types."""
        return (
            'sphinx',
        )

    def get_valid_python_versions(self):
        """Get all valid python versions."""
        try:
            return self.env_config['python']['supported_versions']
        except (KeyError, TypeError):
            pass
        return self.PYTHON_SUPPORTED_VERSIONS

    def get_valid_formats(self):  # noqa
        """Get all valid documentation formats."""
        return (
            'htmlzip',
            'pdf',
            'epub',
        )

    def validate(self):
        """
        Validate and process ``raw_config`` and ``env_config`` attributes.

        It makes sure that:

        - ``type`` is set and is a valid builder
        - ``base`` is a valid directory and defaults to the directory of the
          ``readthedocs.yml`` config file if not set
        """
        # Validate env_config.
        # TODO: this isn't used
        self._config['output_base'] = self.validate_output_base()

        # Validate the build environment first
        # Must happen before `validate_python`!
        self._config['build'] = self.validate_build()

        # Validate raw_config. Order matters.
        # TODO: this isn't used
        self._config['name'] = self.validate_name()
        # TODO: this isn't used
        self._config['type'] = self.validate_type()
        # TODO: this isn't used
        self._config['base'] = self.validate_base()
        self._config['python'] = self.validate_python()
        self._config['formats'] = self.validate_formats()

        self._config['conda'] = self.validate_conda()
        self._config['requirements_file'] = self.validate_requirements_file()
        # TODO: this isn't used
        self._config['conf_file'] = self.validate_conf_file()

    def validate_output_base(self):
        """Validates that ``output_base`` exists and set its absolute path."""
        assert 'output_base' in self.env_config, (
               '"output_base" required in "env_config"')
        base_path = os.path.dirname(self.source_file)
        output_base = os.path.abspath(
            os.path.join(
                self.env_config.get('output_base', base_path),
            )
        )
        return output_base

    def validate_name(self):
        """Validates that name exists."""
        name = self.raw_config.get('name', None)
        if not name:
            name = self.env_config.get('name', None)
        if not name:
            self.error('name', self.NAME_REQUIRED_MESSAGE, code=NAME_REQUIRED)
        name_re = r'^[-_.0-9a-zA-Z]+$'
        if not re.match(name_re, name):
            self.error(
                'name',
                self.NAME_INVALID_MESSAGE.format(
                    name=name,
                    name_re=name_re),
                code=NAME_INVALID)

        return name

    def validate_type(self):
        """Validates that type is a valid choice."""
        type_ = self.raw_config.get('type', None)
        if not type_:
            type_ = self.env_config.get('type', None)
        if not type_:
            self.error('type', self.TYPE_REQUIRED_MESSAGE, code=TYPE_REQUIRED)

        with self.catch_validation_error('type'):
            validate_choice(type_, self.get_valid_types())

        return type_

    def validate_base(self):
        """Validates that path is a valid directory."""
        if 'base' in self.raw_config:
            base = self.raw_config['base']
        else:
            base = os.path.dirname(self.source_file)
        with self.catch_validation_error('base'):
            base_path = os.path.dirname(self.source_file)
            base = validate_directory(base, base_path)
        return base

    def validate_build(self):
        """
        Validate the build config settings.

        This is a bit complex,
        so here is the logic:

        * We take the default image & version if it's specific in the environment
        * Then update the _version_ from the users config
        * Then append the default _image_, since users can't change this
        * Then update the env_config with the settings for that specific image
           - This is currently used for a build image -> python version mapping

        This means we can use custom docker _images_,
        but can't change the supported _versions_ that users have defined.
        """
        # Defaults
        if 'build' in self.env_config:
            build = self.env_config['build'].copy()
        else:
            build = {'image': DOCKER_IMAGE}

        # User specified
        if 'build' in self.raw_config:
            _build = self.raw_config['build']
            if 'image' in _build:
                with self.catch_validation_error('build'):
                    build['image'] = validate_choice(
                        str(_build['image']),
                        self.DOCKER_SUPPORTED_VERSIONS,
                    )
            if ':' not in build['image']:
                # Prepend proper image name to user's image name
                build['image'] = '{}:{}'.format(
                    DOCKER_DEFAULT_IMAGE,
                    build['image']
                )
        # Update docker default settings from image name
        if build['image'] in DOCKER_IMAGE_SETTINGS:
            self.env_config.update(
                DOCKER_IMAGE_SETTINGS[build['image']]
            )
        # Update docker settings from user config
        if 'DOCKER_IMAGE_SETTINGS' in self.env_config and \
                build['image'] in self.env_config['DOCKER_IMAGE_SETTINGS']:
            self.env_config.update(
                self.env_config['DOCKER_IMAGE_SETTINGS'][build['image']]
            )

        # Allow to override specific project
        config_image = self.defaults.get('build_image')
        if config_image:
            build['image'] = config_image
        return build

    def validate_python(self):
        """Validates the ``python`` key, set default values it's necessary."""
        install_project = self.defaults.get('install_project', False)
        use_system_packages = self.defaults.get('use_system_packages', False)
        version = self.defaults.get('python_version', 2)
        python = {
            'use_system_site_packages': use_system_packages,
            'pip_install': False,
            'extra_requirements': [],
            'setup_py_install': install_project,
            'setup_py_path': os.path.join(
                os.path.dirname(self.source_file),
                'setup.py'),
            'version': version,
        }

        if 'python' in self.raw_config:
            raw_python = self.raw_config['python']
            if not isinstance(raw_python, dict):
                self.error(
                    'python',
                    self.PYTHON_INVALID_MESSAGE,
                    code=PYTHON_INVALID)

            # Validate use_system_site_packages.
            if 'use_system_site_packages' in raw_python:
                with self.catch_validation_error(
                        'python.use_system_site_packages'):
                    python['use_system_site_packages'] = validate_bool(
                        raw_python['use_system_site_packages'])

            # Validate pip_install.
            if 'pip_install' in raw_python:
                with self.catch_validation_error('python.pip_install'):
                    python['pip_install'] = validate_bool(
                        raw_python['pip_install'])

            # Validate extra_requirements.
            if 'extra_requirements' in raw_python:
                raw_extra_requirements = raw_python['extra_requirements']
                if not isinstance(raw_extra_requirements, list):
                    self.error(
                        'python.extra_requirements',
                        self.PYTHON_EXTRA_REQUIREMENTS_INVALID_MESSAGE,
                        code=PYTHON_INVALID)
                for extra_name in raw_extra_requirements:
                    with self.catch_validation_error(
                            'python.extra_requirements'):
                        python['extra_requirements'].append(
                            validate_string(extra_name))

            # Validate setup_py_install.
            if 'setup_py_install' in raw_python:
                with self.catch_validation_error('python.setup_py_install'):
                    python['setup_py_install'] = validate_bool(
                        raw_python['setup_py_install'])

            # Validate setup_py_path.
            if 'setup_py_path' in raw_python:
                with self.catch_validation_error('python.setup_py_path'):
                    base_path = os.path.dirname(self.source_file)
                    python['setup_py_path'] = validate_file(
                        raw_python['setup_py_path'], base_path)

            if 'version' in raw_python:
                with self.catch_validation_error('python.version'):
                    # Try to convert strings to an int first, to catch '2', then
                    # a float, to catch '2.7'
                    version = raw_python['version']
                    if isinstance(version, six.string_types):
                        try:
                            version = int(version)
                        except ValueError:
                            try:
                                version = float(version)
                            except ValueError:
                                pass
                    python['version'] = validate_choice(
                        version,
                        self.get_valid_python_versions(),
                    )

        return python

    def validate_conda(self):
        """Validates the ``conda`` key."""
        conda = {}

        if 'conda' in self.raw_config:
            raw_conda = self.raw_config['conda']
            if not isinstance(raw_conda, dict):
                self.error(
                    'conda',
                    self.PYTHON_INVALID_MESSAGE,
                    code=PYTHON_INVALID)

            if 'file' in raw_conda:
                with self.catch_validation_error('conda.file'):
                    base_path = os.path.dirname(self.source_file)
                    conda['file'] = validate_file(
                        raw_conda['file'], base_path)

            return conda
        return None

    def validate_requirements_file(self):
        """Validates that the requirements file exists."""
        if 'requirements_file' not in self.raw_config:
            requirements_file = self.defaults.get('requirements_file')
        else:
            requirements_file = self.raw_config['requirements_file']
        if not requirements_file:
            return None
        base_path = os.path.dirname(self.source_file)
        with self.catch_validation_error('requirements_file'):
            validate_file(requirements_file, base_path)
        return requirements_file

    def validate_conf_file(self):
        """Validates the conf.py file for sphinx."""
        if 'conf_file' not in self.raw_config:
            return None

        conf_file = self.raw_config['conf_file']
        base_path = os.path.dirname(self.source_file)
        with self.catch_validation_error('conf_file'):
            validate_file(conf_file, base_path)
        return conf_file

    def validate_formats(self):
        """Validates that formats contains only valid formats."""
        formats = self.raw_config.get('formats')
        if formats is None:
            return self.defaults.get('formats', [])
        if formats == ['none']:
            return []

        with self.catch_validation_error('format'):
            validate_list(formats)
            for format_ in formats:
                validate_choice(format_, self.get_valid_formats())

        return formats

    @property
    def name(self):
        """The project name."""
        return self._config['name']

    @property
    def base(self):
        """The base directory."""
        return self._config['base']

    @property
    def output_base(self):
        """The output base"""
        return self._config['output_base']

    @property
    def type(self):
        """The documentation type."""
        return self._config['type']

    @property
    def formats(self):
        """The documentation formats to be built."""
        return self._config['formats']

    @property
    def python(self):
        """Python related configuration."""
        return self._config.get('python', {})

    @property
    def python_version(self):
        """Python version."""
        return self._config['python']['version']

    @property
    def pip_install(self):
        """True if the project should be installed using pip."""
        return self._config['python']['pip_install']

    @property
    def install_project(self):
        """True if the project should be installed."""
        if self.pip_install:
            return True
        return self._config['python']['setup_py_install']

    @property
    def extra_requirements(self):
        """Extra requirements to be installed with pip."""
        if self.pip_install:
            return self._config['python']['extra_requirements']
        return []

    @property
    def use_system_site_packages(self):
        """True if the project should have access to the system packages."""
        return self._config['python']['use_system_site_packages']

    @property
    def use_conda(self):
        """True if the project use Conda."""
        return self._config.get('conda') is not None

    @property
    def conda_file(self):
        """The Conda environment file."""
        if self.use_conda:
            return self._config['conda'].get('file')
        return None

    @property
    def requirements_file(self):
        """The project requirements file."""
        return self._config['requirements_file']

    @property
    def build_image(self):
        """The docker image used by the builders."""
        return self._config['build']['image']


class ProjectConfig(list):

    """Wrapper for multiple build configs."""

    def validate(self):
        """Validates each configuration build."""
        for build in self:
            build.validate()


def load(path, env_config):
    """
    Load a project configuration and the top-most build config for a given path.

    That is usually the root of the project, but will look deeper.
    The config will be validated.
    """
    filename = find_one(path, CONFIG_FILENAMES)

    if not filename:
        files = '{}'.format(', '.join(map(repr, CONFIG_FILENAMES[:-1])))
        if files:
            files += ' or '
        files += '{!r}'.format(CONFIG_FILENAMES[-1])
        raise ConfigError('No files {} found'.format(files),
                          code=CONFIG_REQUIRED)
    build_configs = []
    with open(filename, 'r') as configuration_file:
        try:
            configs = parse(configuration_file.read())
        except ParseError as error:
            raise ConfigError(
                'Parse error in {filename}: {message}'.format(
                    filename=filename,
                    message=str(error)),
                code=CONFIG_SYNTAX_INVALID)
        for i, config in enumerate(configs):
            build_config = BuildConfig(
                env_config,
                config,
                source_file=filename,
                source_position=i)
            build_configs.append(build_config)

    project_config = ProjectConfig(build_configs)
    project_config.validate()
    return project_config
