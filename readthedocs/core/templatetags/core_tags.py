"""Template tags for core app."""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

import yaml
from django import template
from django.core.serializers.json import DjangoJSONEncoder
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
def make_document_url(project, version=None, page='', path=''):
    """
    Create a URL for a Project, Version and page (and/or path).

    :param page: is the name of the document as Sphinx call it (e.g.
        /config-file/v1) (note that the extension is not present)
    :param path: is the full path of the page (e.g. /section/configuration.html)

    :returns: URL to the page (e.g. https://docs.domain.com/en/latest/section/configuration.html)
    """
    if not project:
        return ''
    filename = path or page
    return resolve(project=project, version_slug=version, filename=filename)


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


domains_file = Path(__file__).parent / '../../../all_rtd_domains.yaml'
domains_to_migrate = set(yaml.safe_load(domains_file.open()).keys())


@register.simple_tag
def deprecated_domains(user):
    """List all domains from user using a deprecated or unsupported way of creating a custom domain."""
    domains = []
    for project in user.projects:
        for domainobj in project.domains:
            if domainobj.domain in domains_to_migrate:
                domains.append(domainobj)
    return domains
