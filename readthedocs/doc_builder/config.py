"""An API to load config from a readthedocs.yml file."""

from os import path

from readthedocs.config import BuildConfigV1
from readthedocs.config import load as load_config
from readthedocs.projects.models import ProjectConfigurationError

from ..config.config import DefaultConfigFileNotFound
from .constants import DOCKER_IMAGE, DOCKER_IMAGE_SETTINGS


def load_yaml_config(version, readthedocs_yaml_path=None):
    """
    Load a build configuration file (`.readthedocs.yaml`).

    This uses the configuration logic from `readthedocs-build`, which will keep
    parsing consistent between projects.

    :param readthedocs_yaml_path: Optionally, we are told which readthedocs_yaml_path to
                                  load instead of using defaults.
    """
    checkout_path = version.project.checkout_path(version.slug)
    project = version.project

    # Get build image to set up the python version validation. Pass in the
    # build image python limitations to the loaded config so that the versions
    # can be rejected at validation

    img_name = project.container_image or DOCKER_IMAGE
    python_version = '3' if project.python_interpreter == 'python3' else '2'
    try:
        sphinx_configuration = path.join(
            version.get_conf_py_path(),
            'conf.py',
        )
    except ProjectConfigurationError:
        sphinx_configuration = None

    env_config = {
        'build': {
            'image': img_name,
        },
        'defaults': {
            'install_project': project.install_project,
            'formats': get_default_formats(project),
            'requirements_file': project.requirements_file,
            'python_version': python_version,
            'sphinx_configuration': sphinx_configuration,
            'build_image': project.container_image,
            'doctype': project.documentation_type,
        },
    }
    img_settings = DOCKER_IMAGE_SETTINGS.get(img_name, None)
    if img_settings:
        env_config.update(img_settings)

    try:
        config = load_config(
            path=checkout_path,
            env_config=env_config,
            readthedocs_yaml_path=readthedocs_yaml_path,
        )
    except DefaultConfigFileNotFound:
        # Default to use v1 with some defaults from the web interface
        # if we don't find a configuration file.
        config = BuildConfigV1(
            env_config=env_config,
            raw_config={},
            base_path=checkout_path,
            source_file=None,
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
