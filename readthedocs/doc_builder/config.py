# -*- coding: utf-8 -*-
"""An API to load config from a readthedocs.yml file."""

from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from os import path

from readthedocs.config import BuildConfigV1, ConfigError, InvalidConfig
from readthedocs.config import load as load_config
from readthedocs.projects.models import Feature, ProjectConfigurationError

from .constants import DOCKER_IMAGE, DOCKER_IMAGE_SETTINGS


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

    img_name = project.container_image or DOCKER_IMAGE
    python_version = 3 if project.python_interpreter == 'python3' else 2
    allow_v2 = project.has_feature(Feature.ALLOW_V2_CONFIG_FILE)
    try:
        sphinx_configuration = path.join(
            version.get_conf_py_path(),
            'conf.py'
        )
    except ProjectConfigurationError:
        sphinx_configuration = None

    env_config = {
        'allow_v2': allow_v2,
        'build': {
            'image': img_name,
        },
        'output_base': '',
        'name': version.slug,
        'defaults': {
            'install_project': project.install_project,
            'formats': get_default_formats(project),
            'use_system_packages': project.use_system_packages,
            'requirements_file': project.requirements_file,
            'python_version': python_version,
            'sphinx_configuration': sphinx_configuration,
            'build_image': project.container_image,
            'doctype': project.documentation_type,
        }
    }
    img_settings = DOCKER_IMAGE_SETTINGS.get(img_name, None)
    if img_settings:
        env_config.update(img_settings)
        env_config['DOCKER_IMAGE_SETTINGS'] = img_settings

    try:
        config = load_config(
            path=checkout_path,
            env_config=env_config,
        )[0]
    except InvalidConfig:
        # This is a subclass of ConfigError, so has to come first
        raise
    except ConfigError:
        config = BuildConfigV1(
            env_config=env_config,
            raw_config={},
            source_file=checkout_path,
            source_position=0,
        )
        config.validate()
    return config


def get_default_formats(project):
    """Get a list of the default formats for ``project``."""
    formats = ['htmlzip']
    if project.enable_epub_build:
        formats += ['epub']
    if project.enable_pdf_build:
        formats += ['pdf']
    return formats
