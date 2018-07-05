# -*- coding: utf-8 -*-
"""An API to load config from a readthedocs.yml file."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from builtins import object

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
        return self._yaml_config.extra_requirements

    @property
    def python_interpreter(self):
        return self._yaml_config.python_interpreter

    @property
    def python_version(self):
        return self._yaml_config.python_version

    @property
    def python_full_version(self):
        return self._yaml_config.python_full_version

    @property
    def use_system_site_packages(self):
        return self._yaml_config.use_system_site_packages

    @property
    def use_conda(self):
        return self._yaml_config.use_conda

    @property
    def conda_file(self):
        return self._yaml_config.conda_file

    @property
    def requirements_file(self):
        return self._yaml_config.requirements_file

    @property
    def formats(self):
        return self._yaml_config.formats

    @property
    def build_image(self):
        return self._yaml_config.build_image

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
    python_version = 3 if project.python_interpreter == 'python3' else 2
    env_config = {
        'build': {
            'image': img_name,
        },
        'defaults': {
            'install_project': project.install_project,
            'formats': get_default_formats(project),
            'use_system_packages': project.use_system_packages,
            'requirements_file': project.requirements_file,
            'python_version': python_version,
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
        # TODO: this shouldn't be hardcoded here
        env_config.update({
            'output_base': '',
            'type': 'sphinx',
            'name': version.slug,
        })
        config = BuildConfig(
            env_config=env_config,
            raw_config={},
            source_file='empty',
            source_position=0,
        )
        config.validate()
    return ConfigWrapper(version=version, yaml_config=config)


def get_default_formats(project):
    """Get a list of the default formats for ``project``."""
    formats = ['htmlzip']
    if project.enable_epub_build:
        formats += ['epub']
    if project.enable_pdf_build:
        formats += ['pdf']
    return formats
