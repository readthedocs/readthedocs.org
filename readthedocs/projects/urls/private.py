from django.conf.urls import patterns, url

from projects.views.private import AliasList, ProjectDashboard

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    '',
    url(r'^$',
        ProjectDashboard.as_view(),
        name='projects_dashboard'),

    url(r'^import/$',
        'projects.views.private.project_import',
        name='projects_import'),

    url(r'^(?P<project_slug>[-\w]+)/$',
        'projects.views.private.project_manage',
        name='projects_manage'),

    url(r'^(?P<project_slug>[-\w]+)/alias/(?P<id>\d+)/',
        'projects.views.private.edit_alias',
        name='projects_alias_edit'),

    url(r'^(?P<project_slug>[-\w]+)/alias/$',
        'projects.views.private.edit_alias',
        name='projects_alias_create'),

    url(r'^(?P<project_slug>[-\w]+)/alias/list/$',
        AliasList.as_view(),
        name='projects_alias_list'),

    url(r'^(?P<project_slug>[-\w]+)/edit/$',
        'projects.views.private.project_edit',
        name='projects_edit'),

    url(r'^(?P<project_slug>[-\w]+)/advanced/$',
        'projects.views.private.project_advanced',
        name='projects_advanced'),

    url(r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[-\w.]+)/$',
        'projects.views.private.project_version_detail',
        name='project_version_detail'),

    url(r'^(?P<project_slug>[-\w]+)/versions/$',
        'projects.views.private.project_versions',
        name='projects_versions'),

    url(r'^(?P<project_slug>[-\w]+)/delete/$',
        'projects.views.private.project_delete',
        name='projects_delete'),

    url(r'^(?P<project_slug>[-\w]+)/subprojects/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        'projects.views.private.project_subprojects_delete',
        name='projects_subprojects_delete'),

    url(r'^(?P<project_slug>[-\w]+)/subprojects/$',
        'projects.views.private.project_subprojects',
        name='projects_subprojects'),

    url(r'^(?P<project_slug>[-\w]+)/users/$',
        'projects.views.private.project_users',
        name='projects_users'),

    url(r'^(?P<project_slug>[-\w]+)/users/delete/$',
        'projects.views.private.project_users_delete',
        name='projects_users_delete'),

    url(r'^(?P<project_slug>[-\w]+)/notifications/$',
        'projects.views.private.project_notifications',
        name='projects_notifications'),

    url(r'^(?P<project_slug>[-\w]+)/notifications/delete/$',
        'projects.views.private.project_notifications_delete',
        name='projects_notification_delete'),

    url(r'^(?P<project_slug>[-\w]+)/translations/$',
        'projects.views.private.project_translations',
        name='projects_translations'),

    url(r'^(?P<project_slug>[-\w]+)/translations/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        'projects.views.private.project_translations_delete',
        name='projects_translations_delete'),

    url(r'^(?P<project_slug>[-\w]+)/redirects/$',
        'projects.views.private.project_redirects',
        name='projects_redirects'),

    url(r'^(?P<project_slug>[-\w]+)/redirects/delete/$',
        'projects.views.private.project_redirects_delete',
        name='projects_redirects_delete'),
)
