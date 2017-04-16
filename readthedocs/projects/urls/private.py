"""Project URLs for authenticated users"""

from django.conf.urls import url

from readthedocs.projects.views import private
from readthedocs.projects.views.private import (
    ProjectDashboard, ImportView,
    ProjectUpdate, ProjectAdvancedUpdate,
    DomainList, DomainCreate, DomainDelete, DomainUpdate,
    IntegrationList, IntegrationExchangeDetail, IntegrationWebhookSync,
    ProjectAdvertisingUpdate)
from readthedocs.projects.backends.views import ImportWizardView, ImportDemoView


urlpatterns = [
    url(r'^$',
        ProjectDashboard.as_view(),
        name='projects_dashboard'),

    url(r'^import/$',
        ImportView.as_view(wizard_class=ImportWizardView),
        {'wizard': ImportWizardView},
        name='projects_import'),

    url(r'^import/manual/$',
        ImportWizardView.as_view(),
        name='projects_import_manual'),

    url(r'^import/manual/demo/$',
        ImportDemoView.as_view(),
        name='projects_import_demo'),

    url(r'^(?P<project_slug>[-\w]+)/$',
        private.project_manage,
        name='projects_manage'),

    url(r'^(?P<project_slug>[-\w]+)/comments_moderation/$',
        private.project_comments_moderation,
        name='projects_comments_moderation'),

    url(r'^(?P<project_slug>[-\w]+)/edit/$',
        ProjectUpdate.as_view(),
        name='projects_edit'),

    url(r'^(?P<project_slug>[-\w]+)/advanced/$',
        ProjectAdvancedUpdate.as_view(),
        name='projects_advanced'),

    url(r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[^/]+)/delete_html/$',
        private.project_version_delete_html,
        name='project_version_delete_html'),

    url(r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[^/]+)/$',
        private.project_version_detail,
        name='project_version_detail'),

    url(r'^(?P<project_slug>[-\w]+)/versions/$',
        private.project_versions,
        name='projects_versions'),

    url(r'^(?P<project_slug>[-\w]+)/delete/$',
        private.project_delete,
        name='projects_delete'),

    url(r'^(?P<project_slug>[-\w]+)/subprojects/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        private.project_subprojects_delete,
        name='projects_subprojects_delete'),

    url(r'^(?P<project_slug>[-\w]+)/subprojects/$',
        private.project_subprojects,
        name='projects_subprojects'),

    url(r'^(?P<project_slug>[-\w]+)/users/$',
        private.project_users,
        name='projects_users'),

    url(r'^(?P<project_slug>[-\w]+)/users/delete/$',
        private.project_users_delete,
        name='projects_users_delete'),

    url(r'^(?P<project_slug>[-\w]+)/notifications/$',
        private.project_notifications,
        name='projects_notifications'),

    url(r'^(?P<project_slug>[-\w]+)/comments/$',
        private.project_comments_settings,
        name='projects_comments'),

    url(r'^(?P<project_slug>[-\w]+)/notifications/delete/$',
        private.project_notifications_delete,
        name='projects_notification_delete'),

    url(r'^(?P<project_slug>[-\w]+)/translations/$',
        private.project_translations,
        name='projects_translations'),

    url(r'^(?P<project_slug>[-\w]+)/translations/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        private.project_translations_delete,
        name='projects_translations_delete'),

    url(r'^(?P<project_slug>[-\w]+)/redirects/$',
        private.project_redirects,
        name='projects_redirects'),

    url(r'^(?P<project_slug>[-\w]+)/redirects/delete/$',
        private.project_redirects_delete,
        name='projects_redirects_delete'),

    url(r'^(?P<project_slug>[-\w]+)/advertising/$',
        ProjectAdvertisingUpdate.as_view(),
        name='projects_advertising'),
]

domain_urls = [
    url(r'^(?P<project_slug>[-\w]+)/domains/$',
        DomainList.as_view(),
        name='projects_domains'),
    url(r'^(?P<project_slug>[-\w]+)/domains/create/$',
        DomainCreate.as_view(),
        name='projects_domains_create'),
    url(r'^(?P<project_slug>[-\w]+)/domains/(?P<domain_pk>[-\w]+)/edit/$',
        DomainUpdate.as_view(),
        name='projects_domains_edit'),
    url(r'^(?P<project_slug>[-\w]+)/domains/(?P<domain_pk>[-\w]+)/delete/$',
        DomainDelete.as_view(),
        name='projects_domains_delete'),
]

urlpatterns += domain_urls

integration_urls = [
    url(r'^(?P<project_slug>[-\w]+)/integrations/$',
        IntegrationList.as_view(),
        name='projects_integrations'),
    url(r'^(?P<project_slug>[-\w]+)/integrations/exchange/(?P<exchange_pk>[-\w]+)/$',
        IntegrationExchangeDetail.as_view(),
        name='projects_integrations_exchange_detail'),
    url(r'^(?P<project_slug>[-\w]+)/integrations/sync/$',
        IntegrationWebhookSync.as_view(),
        name='projects_integrations_sync'),
]

urlpatterns += integration_urls
