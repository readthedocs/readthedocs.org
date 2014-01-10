from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    # base view, flake8 complains if it is on the previous line.
    'projects.views.private',
    url(r'^$',
        'project_dashboard',
        name='projects_dashboard'),

    url(r'^import/$',
        'project_import',
        name='projects_import'),

    url(r'^upload_html/(?P<project_slug>[-\w]+)/$',
        'upload_html',
        name='projects_upload_html'),

    url(r'^export/(?P<project_slug>[-\w]+)/$',
        'export',
        name='projects_export'),

    url(r'^(?P<project_slug>[-\w]+)/$',
        'project_manage',
        name='projects_manage'),

    url(r'^(?P<project_slug>[-\w]+)/alias/(?P<id>\d+)/',
        'edit_alias',
        name='projects_alias_edit'),

    url(r'^(?P<project_slug>[-\w]+)/alias/$',
        'edit_alias',
        name='projects_alias_create'),

    url(r'^(?P<project_slug>[-\w]+)/alias/list/$',
        'list_alias',
        name='projects_alias_list'),

    url(r'^(?P<project_slug>[-\w]+)/edit/$',
        'project_edit',
        name='projects_edit'),

    url(r'^(?P<project_slug>[-\w]+)/advanced/$',
        'project_advanced',
        name='projects_advanced'),

    url(r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[-\w.]+)/$',
        'project_version_detail',
        name='project_version_detail'),

    url(r'^(?P<project_slug>[-\w]+)/versions/$',
        'project_versions',
        name='projects_versions'),

    url(r'^(?P<project_slug>[-\w]+)/delete/$',
        'project_delete',
        name='projects_delete'),

    url(r'^(?P<project_slug>[-\w]+)/subprojects/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        'project_subprojects_delete',
        name='projects_subprojects_delete'),

    url(r'^(?P<project_slug>[-\w]+)/subprojects/$',
        'project_subprojects',
        name='projects_subprojects'),

    url(r'^(?P<project_slug>[-\w]+)/users/$',
        'project_users',
        name='projects_users'),

    url(r'^(?P<project_slug>[-\w]+)/users/delete/$',
        'project_users_delete',
        name='projects_users_delete'),

    url(r'^(?P<project_slug>[-\w]+)/notifications/$',
        'project_notifications',
        name='projects_notifications'),

    url(r'^(?P<project_slug>[-\w]+)/notifications/delete/$',
        'project_notifications_delete',
        name='projects_notification_delete'),

    url(r'^(?P<project_slug>[-\w]+)/translations/$',
        'project_translations',
        name='projects_translations'),

    url(r'^(?P<project_slug>[-\w]+)/translations/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        'project_translations_delete',
        name='projects_translations_delete'),
)
