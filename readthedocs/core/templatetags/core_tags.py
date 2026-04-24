"""Template tags for core app."""

import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

from readthedocs import __version__
from readthedocs.core.forms import RichSelect
from readthedocs.core.resolver import Resolver
from readthedocs.projects.models import Project


register = template.Library()


@register.simple_tag(name="doc_url")
def make_document_url(project, version=None, page="", path=""):
    """
    Create a URL for a Project, Version and page (and/or path).

    :param page: is the name of the document as Sphinx call it (e.g.
        /config-file/v1) (note that the extension is not present)
    :param path: is the full path of the page (e.g. /section/configuration.html)

    :returns: URL to the page (e.g. https://docs.domain.com/en/latest/section/configuration.html)
    """
    if not project:
        return ""
    filename = path or page
    return Resolver().resolve(project=project, version_slug=version, filename=filename)


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
def url_replace(request, field, *values):
    dict_ = request.GET.copy()
    dict_[field] = "".join(values)
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
        ord(">"): "\\u003E",
        ord("<"): "\\u003C",
        ord("&"): "\\u0026",
    }
    return mark_safe(
        json.dumps(
            data,
            cls=DjangoJSONEncoder,
            indent=indent,
        ).translate(_json_script_escapes)
    )


@register.filter
def is_rich_select(field):
    """Field type comparison used by Crispy form templates."""
    return isinstance(field.field.widget, RichSelect)
