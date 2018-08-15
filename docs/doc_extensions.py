"""
Read the Docs documentation extensions for Sphinx

Adds the following roles:

djangosetting
    Output an inline literal of the corresponding setting value. Useful for
    keeping documentation up to date without editing on settings changes.

buildpyversions
    Output a comma separated list of the supported python versions for a
    Read the Docs build image.
"""

from __future__ import division, print_function, unicode_literals

from django.conf import settings
from docutils import nodes, utils

from readthedocs.config.config import (
    DOCKER_DEFAULT_IMAGE, DOCKER_IMAGE_SETTINGS)


def django_setting_role(typ, rawtext, text, lineno, inliner, options=None,
                        content=None):
    """Always up to date Django settings from the application"""
    dj_setting = getattr(settings, utils.unescape(text), 'None')
    node = nodes.literal(dj_setting, dj_setting)
    return [node], []


def python_supported_versions_role(typ, rawtext, text, lineno, inliner,
                                   options=None, content=None):
    """Up to date supported python versions for each build image."""
    image = '{}:{}'.format(DOCKER_DEFAULT_IMAGE, text)
    image_settings = DOCKER_IMAGE_SETTINGS[image]
    python_versions = image_settings['python']['supported_versions']
    node_list = []
    separator = ', '
    for i, version in enumerate(python_versions):
        node_list.append(nodes.literal(version, version))
        if i < len(python_versions) - 1:
            node_list.append(nodes.Text(separator))
    return (node_list, [])


def setup(_):
    from docutils.parsers.rst import roles
    roles.register_local_role(
        'djangosetting',
        django_setting_role
    )
    roles.register_local_role(
        'buildpyversions',
        python_supported_versions_role
    )

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
