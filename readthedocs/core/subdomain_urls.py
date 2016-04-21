from django.conf.urls import url, patterns

from readthedocs.projects.constants import LANGUAGES_REGEX
from readthedocs.urls import urlpatterns as main_patterns

handler500 = 'readthedocs.core.views.server_error'
handler404 = 'readthedocs.core.views.server_error_404'

urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    url(r'^page/(?P<filename>.*)$',
        'readthedocs.core.views.redirect_page_with_filename',
        name='docs_detail'),

    url(r'^$', 'readthedocs.core.views.redirect_project_slug', name='homepage'),
    url(r'', 'readthedocs.core.views.serve_symlink_docs', name='serve_symlink_docs'),
)

urlpatterns += main_patterns
