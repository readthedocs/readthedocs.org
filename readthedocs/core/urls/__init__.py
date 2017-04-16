from django.conf.urls import url

from django_filters import views as django_filters_views

from readthedocs.constants import pattern_opts
from readthedocs.core import views
from readthedocs.core.views import hooks, serve
from readthedocs.builds.filters import VersionFilter
from readthedocs.projects.feeds import LatestProjectsFeed, NewProjectsFeed
from readthedocs.projects.filters import ProjectFilter
from readthedocs.core.views import HomepageView, SupportView


docs_urls = [
    url((r'^docs/(?P<project_slug>{project_slug})/page/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        serve.redirect_page_with_filename,
        name='docs_detail'),

    url((r'^docs/(?P<project_slug>{project_slug})/'
        r'(?:|projects/(?P<subproject_slug>{project_slug})/)$'.format(**pattern_opts)),
        serve.redirect_project_slug,
        name='docs_detail'),

    url((r'^docs/(?P<project_slug>{project_slug})/'
         r'(?:|projects/(?P<subproject_slug>{project_slug})/)'
         r'(?P<lang_slug>{lang_slug})/'
         r'(?P<version_slug>{version_slug})/'
         r'(?P<filename>{filename_slug})'.format(**pattern_opts)),
        serve.serve_docs,
        name='docs_detail'),

    url(r'^docs/$',HomepageView.as_view(), name='homepage'),
]


core_urls = [
    # Hooks
    url(r'^github', hooks.github_build, name='github_build'),
    url(r'^gitlab', hooks.gitlab_build, name='gitlab_build'),
    url(r'^bitbucket', hooks.bitbucket_build, name='bitbucket_build'),
    url((r'^build/'
         r'(?P<project_id_or_slug>{project_slug})'.format(**pattern_opts)),
        hooks.generic_build,
        name='generic_build'),
    # Random other stuff
    url(r'^random/(?P<project_slug>{project_slug})'.format(**pattern_opts),
        views.random_page,
        name='random_page'),
    url(r'^random/$', views.random_page, name='random_page'),
    url((r'^wipe/(?P<project_slug>{project_slug})/'
         r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)),
        views.wipe_version,
        name='wipe_version'),
]

deprecated_urls = [
    url(r'^filter/version/$',
        django_filters_views.object_filter,
        {'filter_class': VersionFilter, 'template_name': 'filter.html'},
        name='filter_version'),
    url(r'^filter/project/$',
        django_filters_views.object_filter,
        {'filter_class': ProjectFilter, 'template_name': 'filter.html'},
        name='filter_project'),

    url(r'^feeds/new/$',
        NewProjectsFeed(),
        name="new_feed"),
    url(r'^feeds/latest/$',
        LatestProjectsFeed(),
        name="latest_feed"),
]
