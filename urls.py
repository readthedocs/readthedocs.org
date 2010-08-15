from django.conf.urls.defaults import *

from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'core.views.homepage'),
    url(r'^projects/', include('projects.urls.public')),
    url(r'^builds/', include('builds.urls')),
    url(r'^bookmarks/', include('bookmarks.urls')),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^dashboard/', include('projects.urls.private')),


    (r'^admin/', include(admin.site.urls)),
    (r'^github', 'core.views.github_build'),

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
