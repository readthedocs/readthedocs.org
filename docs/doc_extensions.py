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
    features_dict = {}
    for feature in Feature.FEATURES:
        features_dict[feature[0].upper()] = feature[1].capitalize()
    dli_list = []
    for feature, desc in features_dict.items():
        term = nodes.term(text=nodes.Text(feature))
        definition = nodes.definition('', nodes.paragraph(text=desc))
        dli = nodes.definition_list_item('', term, definition)
        dli_list.append(dli)
    dl = nodes.definition_list('', *dli_list)
    return [dl], []


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
