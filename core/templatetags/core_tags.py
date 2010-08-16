import urllib

from django import template
from django.utils.hashcompat import hashlib

register = template.Library()

@register.filter
def gravatar(email, size=48):
    """
    hacked from djangosnippets.org, but basically given an email address
    render an img tag with the hashed up bits needed for leetness omgwtfstillreading
    """
    url = "http://www.gravatar.com/avatar.php?%s" % urllib.urlencode({
        'gravatar_id': hashlib.md5(email).hexdigest(), 
        'size': str(size)
    })
    return '<img src="%s" width="%s" height="%s" alt="gravatar" class="gravatar" border="0" />' % (url, size, size)
