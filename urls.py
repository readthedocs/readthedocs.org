from django.conf.urls.defaults import *

from django.contrib import admin
from django.conf import settings
admin.autodiscover()

handler500 = 'core.views.server_error'
handler404 = 'core.views.server_error_404'

urlpatterns = patterns('',
    url(r'^$', 'core.views.homepage'),
    url(r'^projects/', include('projects.urls.public')),
    url(r'^builds/', include('builds.urls')),
    url(r'^bookmarks/', include('bookmarks.urls')),
    url(r'^flagging/', include('basic.flagging.urls')),
    url(r'^views/', include('watching.urls')),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^dashboard/bookmarks/',
        'bookmarks.views.user_bookmark_list',
        name='user_bookmarks'
    ),
    url(r'^dashboard/', include('projects.urls.private')),
    (r'^admin/', include(admin.site.urls)),
    url(r'^github', 'core.views.github_build', name='github_build'),
    url(r'^github/', 'core.views.github_build', name='github_build'),
    url(r'^build/(?P<pk>\d+)', 'core.views.generic_build', name='generic_build'),
    url(r'^build/(?P<pk>\d+)/', 'core.views.generic_build', name='generic_build'),

    url(r'^random', 'core.views.random_page', name='random_page'),

    url(r'^render_header/',
        'core.views.render_header',
        name='render_header'
    ),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(
            regex  = '^%s/(?P<path>.*)$' % settings.MEDIA_URL.strip('/'),
            view   = 'django.views.static.serve',
            kwargs = {'document_root': settings.MEDIA_ROOT},
        )
    )
