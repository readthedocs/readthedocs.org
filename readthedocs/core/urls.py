from django.conf.urls import url, patterns

from readthedocs.constants import pattern_opts
from readthedocs.builds.filters import VersionFilter
from readthedocs.projects.feeds import LatestProjectsFeed, NewProjectsFeed
from readthedocs.projects.filters import ProjectFilter


docs_urls = patterns(
    '',
    # Handle /page/<path> redirects for explicit "latest" version goodness.
    url((r'^docs/(?P<project_slug>{project_slug})/page/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.redirect_page_with_filename',
        name='docs_detail'),

    # Handle single version URLs
    url((r'^docs/(?P<project_slug>{project_slug})/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.serve_symlink_docs',
        name='docs_detail'),
)


core_urls = patterns(
    '',
    url(r'^github', 'readthedocs.core.views.github_build', name='github_build'),
    url(r'^gitlab', 'readthedocs.core.views.gitlab_build', name='gitlab_build'),
    url(r'^bitbucket', 'readthedocs.core.views.bitbucket_build', name='bitbucket_build'),
    url((r'^build/'
         r'(?P<project_id_or_slug>{project_slug})'.format(**pattern_opts)),
        'readthedocs.core.views.generic_build',
        name='generic_build'),
    url(r'^random/(?P<project_slug>{project_slug})'.format(**pattern_opts),
        'readthedocs.core.views.random_page',
        name='random_page'),
    url(r'^random/$', 'readthedocs.core.views.random_page', name='random_page'),
    url(r'^500/$', 'readthedocs.core.views.divide_by_zero', name='divide_by_zero'),
    url((r'^wipe/(?P<project_slug>{project_slug})/'
         r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)),
        'readthedocs.core.views.wipe_version',
        name='wipe_version'),
)

deprecated_urls = patterns(
    '',
    url(r'^filter/version/$',
        'django_filters.views.object_filter',
        {'filter_class': VersionFilter, 'template_name': 'filter.html'},
        name='filter_version'),
    url(r'^filter/project/$',
        'django_filters.views.object_filter',
        {'filter_class': ProjectFilter, 'template_name': 'filter.html'},
        name='filter_project'),

    url(r'^feeds/new/$',
        NewProjectsFeed(),
        name="new_feed"),
    url(r'^feeds/latest/$',
        LatestProjectsFeed(),
        name="latest_feed"),
    url((r'^mlt/(?P<project_slug>{project_slug})/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.morelikethis',
        name='morelikethis'),
)
