"""
Read the Docs documentation extensions for Sphinx

Adds the following roles:

djangosetting
    Output an inline literal of the corresponding setting value. Useful for
    keeping documentation up to date without editing on settings changes.
"""

from docutils import nodes, utils

from django.conf import settings

from readthedocs.projects.models import Feature


def django_setting_role(typ, rawtext, text, lineno, inliner, options=None,
                        content=None):
    """Always up to date Django settings from the application"""
    dj_setting = getattr(settings, utils.unescape(text), 'None')
    node = nodes.literal(dj_setting, dj_setting)
    return [node], []


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
        'featureflags',
        feature_flags_role
    )

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
