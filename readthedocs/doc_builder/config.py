"""An API to load config from a readthedocs.yml file."""
from __future__ import absolute_import

from builtins import (filter, object)

from readthedocs_build.config import (ConfigError, BuildConfig, InvalidConfig,
                                      load as load_config)
from .constants import BUILD_IMAGES, DOCKER_IMAGE


class ConfigWrapper(object):

    """
    A config object that wraps the Project & YAML based configs.

    Gives precedence to YAML, falling back to project if it isn't defined.

    We only currently implement a subset of the existing YAML config.
    This should be the canonical source for our usage of the YAML files,
    never accessing the config object directly.

    """

    def __init__(self, version, yaml_config):
        self._version = version
        self._project = version.project
        self._yaml_config = yaml_config

    @property
    def pip_install(self):
        if 'pip_install' in self._yaml_config.get('python', {}):
            return self._yaml_config['python']['pip_install']
        return False

    @property
    def install_project(self):
        if self.pip_install:
            return True
        if 'setup_py_install' in self._yaml_config.get('python', {}):
            return self._yaml_config['python']['setup_py_install']
        return self._project.install_project

    @property
    def extra_requirements(self):
        if self.pip_install and 'extra_requirements' in self._yaml_config.get(
                'python', {}):
            return self._yaml_config['python']['extra_requirements']
        return []

    @property
    def python_interpreter(self):
        ver = self.python_version
        if ver in [2, 3]:
            # Get the highest version of the major series version if user only
            # gave us a version of '2', or '3'
            ver = max(list(filter(
                lambda x: x < ver + 1,
                self._yaml_config.get_valid_python_versions(),
            )))
        return 'python{0}'.format(ver)

    @property
    def python_version(self):
        # There should always be a version in the YAML config. If the config
        # version is the default response of `2`, then assume we can use the
        # Python.python_interpreter version to infer this value instead.
        version = 2
        if 'version' in self._yaml_config.get('python', {}):
            version = self._yaml_config['python']['version']
        if version == 2 and self._project.python_interpreter == 'python3':
            version = 3
        return version

    @property
    def use_system_site_packages(self):
        if 'use_system_site_packages' in self._yaml_config.get('python', {}):
            return self._yaml_config['python']['use_system_site_packages']
        return self._project.use_system_packages

    @property
    def use_conda(self):
        return 'conda' in self._yaml_config

    @property
    def conda_file(self):
        if 'file' in self._yaml_config.get('conda', {}):
            return self._yaml_config['conda']['file']
        return None

    @property
    def requirements_file(self):
        if 'requirements_file' in self._yaml_config:
            return self._yaml_config['requirements_file']
        return self._project.requirements_file

    @property
    def formats(self):
        if 'formats' in self._yaml_config:
            return self._yaml_config['formats']
        formats = ['htmlzip']
        if self._project.enable_epub_build:
            formats += ['epub']
        if self._project.enable_pdf_build:
            formats += ['pdf']
        return formats

    # Not implemented until we figure out how to keep in sync with the webs.
    # Probably needs to be version-specific as well, not project.
    # @property
    # def documentation_type(self):
    #     if 'type' in self._yaml_config:
    #         return self._yaml_config['type']
    #     else:
    #         return self._project.documentation_type


def load_yaml_config(version):
    """
    Load a configuration from `readthedocs.yml` file.

    This uses the configuration logic from `readthedocs-build`,
    which will keep parsing consistent between projects.
    """
    checkout_path = version.project.checkout_path(version.slug)
    env_config = {}

    # Get build image to set up the python version validation. Pass in the
    # build image python limitations to the loaded config so that the versions
    # can be rejected at validation
    build_image = BUILD_IMAGES.get(
        version.project.container_image,
        BUILD_IMAGES.get(DOCKER_IMAGE, None),
    )
    if build_image:
        env_config = {
            'python': build_image['python'],
        }

    try:
        sphinx_env_config = env_config.copy()
        sphinx_env_config.update({
            'output_base': '',
            'type': 'sphinx',
            'name': version.slug,
        })
        config = load_config(
            path=checkout_path,
            env_config=sphinx_env_config,
        )[0]
    except InvalidConfig:  # This is a subclass of ConfigError, so has to come first
        raise
    except ConfigError:
        config = BuildConfig(
            env_config=env_config,
            raw_config={},
            source_file='empty',
            source_position=0,
        )
    return ConfigWrapper(version=version, yaml_config=config)
