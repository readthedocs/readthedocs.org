"""Template tags for core app."""

from __future__ import absolute_import

import hashlib

from builtins import str  # pylint: disable=redefined-builtin
from django import template
from django.conf import settings
from django.utils.encoding import force_bytes, force_text
from django.utils.safestring import mark_safe
from future.backports.urllib.parse import urlencode

from readthedocs.core.resolver import resolve
from readthedocs.projects.models import Project


register = template.Library()


@register.filter
def gravatar(email, size=48):
    """
    Hacked from djangosnippets.org, but basically given an email address

    render an img tag with the hashed up bits needed for leetness
    omgwtfstillreading
    """
    url = "http://www.gravatar.com/avatar.php?%s" % urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(),
        'size': str(size)
    })
    return ('<img src="%s" width="%s" height="%s" alt="gravatar" '
            'class="gravatar" border="0" />' % (url, size, size))


@register.simple_tag(name="doc_url")
def make_document_url(project, version=None, page=''):
    if not project:
        return ""
    return resolve(project=project, version_slug=version, filename=page)


@register.filter(is_safe=True)
def restructuredtext(value, short=False):
    try:
        from docutils.core import publish_parts
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError(
                "Error in 'restructuredtext' filter: "
                "The Python docutils library isn't installed."
            )
        return force_text(value)
    else:
        docutils_settings = {
            'raw_enabled': False,
            'file_insertion_enabled': False,
        }
        docutils_settings.update(getattr(settings, 'RESTRUCTUREDTEXT_FILTER_SETTINGS', {}))
        parts = publish_parts(source=force_bytes(value), writer_name="html4css1",
                              settings_overrides=docutils_settings)
        out = force_text(parts["fragment"])
        try:
            if short:
                out = out.split("\n")[0]
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
