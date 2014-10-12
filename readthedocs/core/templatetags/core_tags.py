import urllib
import hashlib

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.encoding import force_bytes, force_text

from builds.models import Version
from projects.models import Project

register = template.Library()


@register.filter
def gravatar(email, size=48):
    """hacked from djangosnippets.org, but basically given an email address
    render an img tag with the hashed up bits needed for leetness
    omgwtfstillreading

    """
    url = "http://www.gravatar.com/avatar.php?%s" % urllib.urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(),
        'size': str(size)
    })
    return ('<img src="%s" width="%s" height="%s" alt="gravatar" '
            'class="gravatar" border="0" />' % (url, size, size))


@register.simple_tag(name="doc_url")
def make_document_url(project, version=None, page=None):
    if not project:
        return ""
    if project.main_language_project:
        base_url = project.get_translation_url(version)
    else:
        base_url = project.get_docs_url(version)
    if page and page != "index":
        if project.documentation_type == "sphinx_htmldir":
            path = page + "/"
        elif project.documentation_type == "sphinx_singlehtml":
            path = "index.html#document-" + page
        else:
            path = page + ".html"
    else:
        path = ""
    return base_url + path


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
        docutils_settings = getattr(settings, "RESTRUCTUREDTEXT_FILTER_SETTINGS",
                                    {})
        parts = publish_parts(source=force_bytes(value), writer_name="html4css1",
                              settings_overrides=docutils_settings)
        out = force_text(parts["fragment"])
        try:
            if short:
                out = out.split("\n")[0]
        except IndexError:
            pass
        finally:
            return mark_safe(out)


@register.filter
def get_project(slug):
    try:
        return Project.objects.get(slug=slug)
    except:
        return None


@register.filter
def get_version(slug):
    try:
        return  Project.objects.get(slug=slug)
    except:
        return None


@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()

