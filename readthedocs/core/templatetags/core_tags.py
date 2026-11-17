"""Template tags for core app."""

from django import template

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
def is_rich_select(field):
    """Field type comparison used by Crispy form templates."""
    return isinstance(field.field.widget, RichSelect)
