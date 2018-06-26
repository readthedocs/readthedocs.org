# -*- coding: utf-8 -*-
"""An API to load config from a readthedocs.yml file."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from builtins import filter, object

from readthedocs.config import BuildConfig, ConfigError, InvalidConfig
from readthedocs.config import load as load_config

from .constants import DOCKER_IMAGE, DOCKER_IMAGE_SETTINGS


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
        return self._yaml_config.pip_install

    @property
    def install_project(self):
        return self._yaml_config.install_project

    @property
    def extra_requirements(self):
        try:
            return self._yaml_config.extra_requirements
        except AttributeError as e:
            return []

    @property
    def python_interpreter(self):
        ver = self.python_full_version
        return 'python{0}'.format(ver)

    @property
    def python_version(self):
        # There should always be a version in the YAML config. If the config
        # version is the default response of `2`, then assume we can use the
        # Python.python_interpreter version to infer this value instead.
        version = 2
        if 'version' in self._yaml_config.python:
            version = self._yaml_config.python['version']
        if version == 2 and self._project.python_interpreter == 'python3':
            version = 3
        return version

    @property
    def python_full_version(self):
        ver = self.python_version
        if ver in [2, 3]:
            # Get the highest version of the major series version if user only
            # gave us a version of '2', or '3'
            ver = max(
                list(
                    filter(
                        lambda x: x < ver + 1,
                        self._yaml_config.get_valid_python_versions(),
                    )))
        return ver

    @property
    def use_system_site_packages(self):
        try:
            return self._yaml_config.use_system_site_packages
        except (KeyError, AttributeError) as e:
            return self._project.use_system_packages

    @property
    def use_conda(self):
        return self._yaml_config.use_conda

    @property
    def conda_file(self):
        return self._yaml_config.conda_file

    @property
    def requirements_file(self):
        try:
            if self._yaml_config.requirements_file is not None:
                return self._yaml_config.requirements_file
        except (KeyError, AttributeError) as e:
            pass
        return self._project.requirements_file

    @property
    def formats(self):
        try:
            if self._yaml_config.formats is not None:
                return self._yaml_config.formats
        except KeyError as e:
            pass
        formats = ['htmlzip']
        if self._project.enable_epub_build:
            formats += ['epub']
        if self._project.enable_pdf_build:
            formats += ['pdf']
        return formats

    @property
    def build_image(self):
        if self._project.container_image:
            # Allow us to override per-project still
            return self._project.container_image
        try:
            return self._yaml_config.build_image
        except KeyError as e:
            return None

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

    This uses the configuration logic from `readthedocs-build`, which will keep
    parsing consistent between projects.
    """
    checkout_path = version.project.checkout_path(version.slug)
    project = version.project

    # Get build image to set up the python version validation. Pass in the
    # build image python limitations to the loaded config so that the versions
    # can be rejected at validation

    img_name = version.project.container_image or DOCKER_IMAGE
    env_config = {
        'build': {
            'image': img_name,
        },
        'defaults': {
            'install_project': project.install_project,
        }
    }
    img_settings = DOCKER_IMAGE_SETTINGS.get(img_name, None)
    if img_settings:
        env_config.update(img_settings)
        env_config['DOCKER_IMAGE_SETTINGS'] = img_settings

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
    except InvalidConfig:
        # This is a subclass of ConfigError, so has to come first
        raise
    except ConfigError:
        config = BuildConfig(
            env_config=env_config,
            raw_config={},
            source_file='empty',
            source_position=0,
        )
    return ConfigWrapper(version=version, yaml_config=config)
