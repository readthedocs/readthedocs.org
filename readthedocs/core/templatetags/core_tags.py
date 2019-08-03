"""Template tags for core app."""

import hashlib
import json
from urllib.parse import urlencode

from django import template
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_bytes, force_text
from django.utils.safestring import mark_safe

from readthedocs import __version__
from readthedocs.core.resolver import resolve
from readthedocs.projects.models import Project


register = template.Library()


@register.filter
def gravatar(email, size=48):
    """
    Hacked from djangosnippets.org, but basically given an email address.

    render an img tag with the hashed up bits needed for leetness
    omgwtfstillreading
    """
    url = 'http://www.gravatar.com/avatar.php?%s' % urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(),
        'size': str(size),
    })
    return (
        '<img src="%s" width="%s" height="%s" alt="gravatar" '
        'class="gravatar" border="0" />' % (url, size, size)
    )


@register.simple_tag(name='doc_url')
def make_document_url(project, version=None, page=''):
    if not project:
        return ''
    return resolve(project=project, version_slug=version, filename=page)


@register.filter(is_safe=True)
def restructuredtext(value, short=False):
    try:
        from docutils.core import publish_parts
        from docutils import ApplicationError
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in 'restructuredtext' filter: "
                "The Python docutils library isn't installed.",
            )
        return force_text(value)
    else:
        docutils_settings = {
            'raw_enabled': False,
            'file_insertion_enabled': False,
        }
        docutils_settings.update(
            settings.RESTRUCTUREDTEXT_FILTER_SETTINGS,
        )
        try:
            parts = publish_parts(
                source=force_bytes(value),
                writer_name='html4css1',
                settings_overrides=docutils_settings,
            )
        except ApplicationError:
            return force_text(value)

        out = force_text(parts['fragment'])
        try:
            if short:
                out = out.split('\n')[0]
        except IndexError:
            pass
        return mark_safe(out)


@register.filter
def get_project(slug):
    try:
        return Project.objects.get(slug=slug)
    except Project.DoesNotExist:
        return None


@register.filter
def get_version(slug):
    try:
        return Project.objects.get(slug=slug)
    except Project.DoesNotExist:
        return None


@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.filter
def key(d, key_name):
    return d[key_name]


@register.filter
def get_key_or_none(d, key_name):
    try:
        return d[key_name]
    except KeyError:
        return None


@register.simple_tag
def readthedocs_version():
    return __version__


@register.filter
def escapejson(data, indent=None):
    """
    Escape JSON correctly for inclusion in Django templates.

    This code was mostly taken from Django's implementation
    https://docs.djangoproject.com/en/2.2/ref/templates/builtins/#json-script
    https://github.com/django/django/blob/2.2.2/django/utils/html.py#L74-L92

    After upgrading to Django 2.1+, we could replace this with Django's implementation
    although the inputs and outputs are a bit different.

    Example:

        var jsvar = {{ dictionary_value | escapejson }}
    """
    if indent:
        indent = int(indent)
    _json_script_escapes = {
        ord('>'): '\\u003E',
        ord('<'): '\\u003C',
        ord('&'): '\\u0026',
    }
    return mark_safe(
        json.dumps(
            data,
            cls=DjangoJSONEncoder,
            indent=indent,
        ).translate(_json_script_escapes))
