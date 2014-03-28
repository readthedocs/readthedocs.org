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
def make_document_url(project, version=None, page=None, subproject=False):
    if subproject:
        base_url = "/projects/%s/%s/%s/" % (
            project.slug,
            project.language,
            version if version and version != '' else project.default_version
        )
    elif project.main_language_project:
        base_url =  project.get_translation_url(version)
    else:
        base_url = project.get_docs_url(version)

    if page and page != "index":
        # This logic sholdn't be here because it's document builder specific.
        # Builders should have a format string or a function for building pathes
        # and we should simply use them here.
        if project.documentation_type == "sphinx_htmldir":
            path =  page + "/"
        elif project.documentation_type == "sphinx_singlehtml":
            path = "index.html#document-" + page
        else:
            path =  page + ".html"
    else:
        path = ""
    return base_url + path
