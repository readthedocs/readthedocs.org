from django.conf.urls.defaults import patterns, url
from django.conf import settings


urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    '',
    url(r'build',
        'websupport.views.build',
        name='build'),
    url(r'_has_node',
        'websupport.views.has_node',
        name='has_node'),
    url(r'_add_node',
        'websupport.views.add_node',
        name='add_node'),
    url(r'_add_comment',
        'websupport.views.add_comment',
        name='add_comment'),
    url(r'_get_comments',
        'websupport.views.get_comments',
        name='get_comments'),
    url(r'_get_metadata',
        'websupport.views.get_metadata',
        name='get_metadata'),
    url(r'_get_options',
        'websupport.views.get_options',
        name='get_options'),
    url(r'(?P<file>.*)',
        'websupport.views.serve_file',
        name='serve_file'),
)
