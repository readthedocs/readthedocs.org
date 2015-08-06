from django.conf.urls import url, patterns, include
from django.contrib import admin
from django.conf import settings
from django.views.generic.base import TemplateView

from tastypie.api import Api

from readthedocs.api.base import (ProjectResource, UserResource, BuildResource,
                      VersionResource, FileResource)
from readthedocs.builds.filters import VersionFilter
from readthedocs.builds.version_slug import VERSION_SLUG_REGEX
from readthedocs.core.views import HomepageView, SearchView
from readthedocs.projects.feeds import LatestProjectsFeed, NewProjectsFeed
from readthedocs.projects.filters import ProjectFilter
from readthedocs.projects.constants import LANGUAGES_REGEX
from readthedocs.projects.constants import PROJECT_SLUG_REGEX

v1_api = Api(api_name='v1')
v1_api.register(BuildResource())
v1_api.register(UserResource())
v1_api.register(ProjectResource())
v1_api.register(VersionResource())
v1_api.register(FileResource())

admin.autodiscover()

handler500 = 'readthedocs.core.views.server_error'
handler404 = 'readthedocs.core.views.server_error_404'


pattern_opts = {
    'project_slug': PROJECT_SLUG_REGEX,
    'lang_slug': LANGUAGES_REGEX,
    'version_slug': VERSION_SLUG_REGEX,
    'filename_slug': '(?:.*)',
}


urlpatterns = patterns(
    '',  # base view, flake8 complains if it is on the previous line.
    url(r'^$', HomepageView.as_view(), name='homepage'),
    url(r'^security/', TemplateView.as_view(template_name='security.html')),

    # For serving docs locally and when nginx isn't
    url((r'^docs/(?P<project_slug>{project_slug})/(?P<lang_slug>{lang_slug})/'
         r'(?P<version_slug>{version_slug})/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.serve_docs',
        name='docs_detail'),

    # Redirect to default version, if only lang_slug is set.
    url((r'^docs/(?P<project_slug>{project_slug})/'
         r'(?P<lang_slug>{lang_slug})/$'.format(**pattern_opts)),
        'readthedocs.core.views.redirect_lang_slug',
        name='docs_detail'),

    # Redirect to default version, if only version_slug is set.
    url((r'^docs/(?P<project_slug>{project_slug})/'
         r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)),
        'readthedocs.core.views.redirect_version_slug',
        name='docs_detail'),

    # Redirect to default version.
    url(r'^docs/(?P<project_slug>{project_slug})/$'.format(**pattern_opts),
        'readthedocs.core.views.redirect_project_slug',
        name='docs_detail'),

    # Handle /page/<path> redirects for explicit "latest" version goodness.
    url((r'^docs/(?P<project_slug>{project_slug})/page/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.redirect_page_with_filename',
        name='docs_detail'),

    # Handle single version URLs
    url((r'^docs/(?P<project_slug>{project_slug})/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.serve_single_version_docs',
        name='docs_detail'),

    # Handle fallbacks
    url((r'^user_builds/(?P<project_slug>{project_slug})/rtd-builds/'
         r'(?P<version_slug>{version_slug})/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.server_helpful_404',
        name='user_buils_fallback'),
    url((r'^user_builds/(?P<project_slug>{project_slug})/translations/'
         r'(?P<lang_slug>{lang_slug})/(?P<version_slug>{version_slug})/'
         r'(?P<filename>{filename_slug})$'.format(**pattern_opts)),
        'readthedocs.core.views.server_helpful_404',
        name='user_builds_fallback_translations'),

    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^projects/', include('readthedocs.projects.urls.public')),
    url(r'^builds/', include('readthedocs.builds.urls')),
    url(r'^bookmarks/', include('readthedocs.bookmarks.urls')),
    # Ship elastic search
    url(r'^search/$', 'readthedocs.search.views.elastic_search', name='search'),
    url(r'^elasticsearch/$', 'readthedocs.search.views.elastic_search', name='elastic_search'),
    url(r'^search/project/', SearchView.as_view(), name='haystack_project'),
    #url(r'^search/', include('haystack.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^dashboard/', include('readthedocs.projects.urls.private')),
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
    url(r'^sustainability/', include('readthedocs.donate.urls')),
    url(r'^live/$', 'readthedocs.core.views.live_builds', name='live_builds'),
    url(r'^500/$', 'readthedocs.core.views.divide_by_zero', name='divide_by_zero'),
    url(r'^filter/version/$',
        'django_filters.views.object_filter',
        {'filter_class': VersionFilter, 'template_name': 'filter.html'},
        name='filter_version'),
    url(r'^filter/project/$',
        'django_filters.views.object_filter',
        {'filter_class': ProjectFilter, 'template_name': 'filter.html'},
        name='filter_project'),
    url((r'^wipe/(?P<project_slug>{project_slug})/'
         r'(?P<version_slug>{version_slug})/$'.format(**pattern_opts)),
        'readthedocs.core.views.wipe_version',
        name='wipe_version'),


    url(r'^websupport/', include('readthedocs.comments.urls')),
    url(r'^profiles/', include('readthedocs.profiles.urls.public')),
    url(r'^accounts/', include('readthedocs.profiles.urls.private')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^accounts/gold/', include('readthedocs.gold.urls')),
    url(r'^api/', include(v1_api.urls)),
    url(r'^api/v2/', include('readthedocs.restapi.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
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

if settings.DEBUG:
    urlpatterns += patterns(
        '',  # base view, flake8 complains if it is on the previous line.
        url('style-catalog/$',
            TemplateView.as_view(template_name='style_catalog.html')),
        url(regex='^%s/(?P<path>.*)$' % settings.MEDIA_URL.strip('/'),
            view='django.views.static.serve',
            kwargs={'document_root': settings.MEDIA_ROOT}),
    )
