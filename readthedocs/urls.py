from django.conf.urls.defaults import url, patterns, include
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template

from tastypie.api import Api

from api.base import ProjectResource, UserResource, BuildResource, VersionResource, FileResource
from builds.filters import VersionFilter
from core.forms import UserProfileForm
from core.views import SearchView
from projects.feeds import LatestProjectsFeed, NewProjectsFeed
from projects.filters import ProjectFilter

v1_api = Api(api_name='v1')
v1_api.register(BuildResource())
v1_api.register(UserResource())
v1_api.register(ProjectResource())
v1_api.register(VersionResource())
v1_api.register(FileResource())

admin.autodiscover()

handler500 = 'core.views.server_error'
handler404 = 'core.views.server_error_404'

urlpatterns = patterns('',
    url(r'^$', 'core.views.homepage'),
    url(r'^_admin/', direct_to_template, {'template': 'admin.html'}),

    # For serving docs locally and when nginx isn't
    url(r'^docs/(?P<project_slug>[-\w]+)/(?P<lang_slug>en)/(?P<version_slug>[-._\w]+?)/(?P<filename>.*)$',
        'core.views.serve_docs',
        name='docs_detail'
    ),

    # Redirect to default version.
    url(r'^docs/(?P<project_slug>[-\w]+)/$',
        'core.views.serve_docs',
        {'version_slug': None,
        'lang_slug': None,
        'filename': ''},
        name='docs_detail'
    ),
    url(r'^docs/(?P<project_slug>[-\w]+)/page/(?P<filename>.*)$',
        'core.views.serve_docs',
        {'version_slug': None,
        'lang_slug': None},
        name='docs_detail'
    ),

    #WTF are these both here?
    #url(r'^docs/', include('projects.urls.public')),
    url(r'^projects/', include('projects.urls.public')),
    url(r'^builds/', include('builds.urls')),
    url(r'^flagging/', include('basic.flagging.urls')),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^search/project/', SearchView.as_view(), name='haystack_project'),
    url(r'^search/', include('haystack.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^dashboard/', include('projects.urls.private')),
    url(r'^github', 'core.views.github_build', name='github_build'),
    url(r'^bitbucket', 'core.views.bitbucket_build', name='bitbucket_build'),
    url(r'^build/(?P<pk>\d+)', 'core.views.generic_build', name='generic_build'),
    url(r'^random/(?P<project>[\w-]+)', 'core.views.random_page', name='random_page'),
    url(r'^random/$', 'core.views.random_page', name='random_page'),
    url(r'^depth/$', 'core.views.queue_depth', name='queue_depth'),
    url(r'^live/$', 'core.views.live_builds', name='live_builds'),
    url(r'^filter/version/$',
        'django_filters.views.object_filter',
        { 'filter_class': VersionFilter, 'template_name': 'filter.html' },
        name='filter_version'
    ),
    url(r'^filter/project/$',
        'django_filters.views.object_filter',
        { 'filter_class': ProjectFilter, 'template_name': 'filter.html' },
        name='filter_project'
    ),
    url(r'^wipe/(?P<project_slug>[-\w]+)/(?P<version_slug>[-\w]+)/$',
        'core.views.wipe_version',
        name='wipe_version'
    ),
    url(r'^profiles/create/', 'profiles.views.create_profile',
        {'form_class': UserProfileForm},
       name='profiles_profile_create'),
    url(r'^profiles/edit/', 'profiles.views.edit_profile',
        {'form_class': UserProfileForm},
       name='profiles_profile_edit'),
    url(r'^profiles/', include('profiles.urls')),
    url(r'^api/', include(v1_api.urls)),
    url(r'^feeds/new/$',
        NewProjectsFeed(),
        name="new_feed"),
    url(r'^feeds/latest/$',
        LatestProjectsFeed(),
        name="latest_feed"),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(
            regex  = '^%s/(?P<path>.*)$' % settings.MEDIA_URL.strip('/'),
            view   = 'django.views.static.serve',
            kwargs = {'document_root': settings.MEDIA_ROOT},
        )
    )
