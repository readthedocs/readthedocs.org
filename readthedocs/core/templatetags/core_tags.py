import urllib

from django import template
from django.utils.hashcompat import hashlib

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
    if project.main_language_project:
        base_url =  project.get_translation_url(version)
    else:
        base_url = project.get_docs_url(version)
    ending = "/" if project.documentation_type == "sphinx_htmldir" else ".html"
    return base_url + ((page + ending) if page != "index" else "")
