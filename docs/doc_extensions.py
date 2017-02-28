"""
Read the Docs documentation extensions for Sphinx

Adds the following roles:

djangosetting
    Output an inline literal of the corresponding setting value. Useful for
    keeping documentation up to date without editing on settings changes.
"""

from docutils import nodes, utils

from django.conf import settings


def django_setting_role(typ, rawtext, text, lineno, inliner, options=None,
                        content=None):
    """Always up to date Django settings from the application"""
    dj_setting = getattr(settings, utils.unescape(text), 'None')
    node = nodes.literal(dj_setting, dj_setting)
    return [node], []


def setup(_):
    from docutils.parsers.rst import roles
    roles.register_local_role('djangosetting', django_setting_role)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
