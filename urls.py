from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^dashboard/', include('projects.urls.private')),
    url(r'^projects/(?P<username>\w+)/(?P<project_slug>[-\w]+)/docs/(?P<filename>.*)$',
        'core.views.serve_docs',
        name='projects_docs'
    ),
    url(r'^projects/', include('projects.urls.public')),
    (r'^admin/', include(admin.site.urls)),
    (r'^github', 'core.views.github_build'),
)
