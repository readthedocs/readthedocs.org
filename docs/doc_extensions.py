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

from django.conf import settings
from docutils import nodes, utils

from readthedocs.projects.models import Feature


def django_setting_role(typ, rawtext, text, lineno, inliner, options=None,
                        content=None):
    """Always up to date Django settings from the application"""
    dj_setting = getattr(settings, utils.unescape(text), 'None')
    node = nodes.literal(dj_setting, dj_setting)
    return [node], []


def python_supported_versions_role(typ, rawtext, text, lineno, inliner,
                                   options=None, content=None):
    """Up to date supported python versions for each build image."""
    image = '{}:{}'.format(settings.DOCKER_DEFAULT_IMAGE, text)
    image_settings = settings.DOCKER_IMAGE_SETTINGS[image]
    python_versions = image_settings['python']['supported_versions']
    node_list = []
    separator = ', '
    for i, version in enumerate(python_versions):
        node_list.append(nodes.literal(version, version))
        if i < len(python_versions) - 1:
            node_list.append(nodes.Text(separator))
    return (node_list, [])


def feature_flags_role(typ, rawtext, text, lineno, inliner, options=None,
                       content=None):
    """Up to date feature flags from the application."""
    all_features = Feature.FEATURES
    requested_feature = utils.unescape(text)
    for feature in all_features:
        if requested_feature.lower() == feature[0].lower():
            desc = nodes.Text(feature[1], feature[1])
    return [desc], []


def setup(_):
    from docutils.parsers.rst import roles
    roles.register_local_role(
        'djangosetting',
        django_setting_role
    )
    roles.register_local_role(
        'buildpyversions',
        python_supported_versions_role,
    )
    roles.register_local_role(
        'featureflags',
        feature_flags_role,
    )

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
