"""Project URLs for authenticated users."""

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView

from readthedocs.constants import pattern_opts
from readthedocs.projects.backends.views import ImportDemoView, ImportWizardView
from readthedocs.projects.views import private
from readthedocs.projects.views.private import (
    DomainCreate,
    DomainDelete,
    DomainList,
    DomainUpdate,
    EnvironmentVariableCreate,
    EnvironmentVariableDelete,
    EnvironmentVariableDetail,
    EnvironmentVariableList,
    ImportView,
    IntegrationCreate,
    IntegrationDelete,
    IntegrationDetail,
    IntegrationExchangeDetail,
    IntegrationList,
    IntegrationWebhookSync,
    ProjectAdvancedUpdate,
    ProjectAdvertisingUpdate,
    ProjectDashboard,
    ProjectDelete,
    ProjectNotications,
    ProjectNoticationsDelete,
    ProjectRedirects,
    ProjectRedirectsDelete,
    ProjectTranslationsDelete,
    ProjectTranslationsListAndCreate,
    ProjectUpdate,
    ProjectUsersCreateList,
    ProjectUsersDelete,
    ProjectVersionDeleteHTML,
    ProjectVersionDetail,
    SearchAnalytics,
)

urlpatterns = [
    url(r'^$', ProjectDashboard.as_view(), name='projects_dashboard'),
    url(
        r'^import/$', ImportView.as_view(wizard_class=ImportWizardView),
        {'wizard': ImportWizardView}, name='projects_import',
    ),
    url(
        r'^import/manual/$', ImportWizardView.as_view(),
        name='projects_import_manual',
    ),
    url(
        r'^import/manual/demo/$', ImportDemoView.as_view(),
        name='projects_import_demo',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/$',
        login_required(
            RedirectView.as_view(pattern_name='projects_detail', permanent=True),
        ),
        name='projects_manage',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/edit/$', ProjectUpdate.as_view(),
        name='projects_edit',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/advanced/$',
        ProjectAdvancedUpdate.as_view(), name='projects_advanced',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[^/]+)/delete_html/$',
        ProjectVersionDeleteHTML.as_view(),
        name='project_version_delete_html',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[^/]+)/$',
        ProjectVersionDetail.as_view(),
        name='project_version_detail',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/delete/$',
        ProjectDelete.as_view(),
        name='projects_delete',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/users/$',
        ProjectUsersCreateList.as_view(),
        name='projects_users',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/users/delete/$',
        ProjectUsersDelete.as_view(),
        name='projects_users_delete',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/notifications/$',
        ProjectNotications.as_view(),
        name='projects_notifications',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/notifications/delete/$',
        ProjectNoticationsDelete.as_view(),
        name='projects_notification_delete',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/translations/$',
        ProjectTranslationsListAndCreate.as_view(),
        name='projects_translations',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/translations/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        ProjectTranslationsDelete.as_view(),
        name='projects_translations_delete',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/redirects/$',
        ProjectRedirects.as_view(),
        name='projects_redirects',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/redirects/delete/$',
        ProjectRedirectsDelete.as_view(),
        name='projects_redirects_delete',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/advertising/$',
        ProjectAdvertisingUpdate.as_view(), name='projects_advertising',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/search-analytics/$',
        SearchAnalytics.as_view(),
        name='projects_search_analytics',
        ),
]

domain_urls = [
    url(
        r'^(?P<project_slug>[-\w]+)/domains/$',
        DomainList.as_view(),
        name='projects_domains',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/domains/create/$',
        DomainCreate.as_view(),
        name='projects_domains_create',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/domains/(?P<domain_pk>[-\w]+)/edit/$',
        DomainUpdate.as_view(),
        name='projects_domains_edit',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/domains/(?P<domain_pk>[-\w]+)/delete/$',
        DomainDelete.as_view(),
        name='projects_domains_delete',
    ),
]

urlpatterns += domain_urls

integration_urls = [
    url(
        r'^(?P<project_slug>{project_slug})/integrations/$'.format(
            **pattern_opts
        ),
        IntegrationList.as_view(),
        name='projects_integrations',
    ),
    url(
        r'^(?P<project_slug>{project_slug})/integrations/sync/$'.format(
            **pattern_opts
        ),
        IntegrationWebhookSync.as_view(),
        name='projects_integrations_webhooks_sync',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/integrations/create/$'.format(
                **pattern_opts
            )
        ),
        IntegrationCreate.as_view(),
        name='projects_integrations_create',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'integrations/(?P<integration_pk>{integer_pk})/$'.format(
                **pattern_opts
            )
        ),
        IntegrationDetail.as_view(),
        name='projects_integrations_detail',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'integrations/(?P<integration_pk>{integer_pk})/'
            r'exchange/(?P<exchange_pk>[-\w]+)/$'.format(**pattern_opts)
        ),
        IntegrationExchangeDetail.as_view(),
        name='projects_integrations_exchanges_detail',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'integrations/(?P<integration_pk>{integer_pk})/sync/$'.format(
                **pattern_opts
            )
        ),
        IntegrationWebhookSync.as_view(),
        name='projects_integrations_webhooks_sync',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'integrations/(?P<integration_pk>{integer_pk})/delete/$'.format(
                **pattern_opts
            )
        ),
        IntegrationDelete.as_view(),
        name='projects_integrations_delete',
    ),
]

urlpatterns += integration_urls

subproject_urls = [
    url(
        r'^(?P<project_slug>{project_slug})/subprojects/$'.format(
            **pattern_opts
        ),
        private.ProjectRelationshipList.as_view(),
        name='projects_subprojects',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/subprojects/create/$'.format(
                **pattern_opts
            )
        ),
        private.ProjectRelationshipCreate.as_view(),
        name='projects_subprojects_create',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'subprojects/(?P<subproject_slug>{project_slug})/edit/$'.format(
                **pattern_opts
            )
        ),
        private.ProjectRelationshipUpdate.as_view(),
        name='projects_subprojects_update',
    ),
    url(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'subprojects/(?P<subproject_slug>{project_slug})/delete/$'.format(
                **pattern_opts
            )
        ),
        private.ProjectRelationshipDelete.as_view(),
        name='projects_subprojects_delete',
    ),
]

urlpatterns += subproject_urls

environmentvariable_urls = [
    url(
        r'^(?P<project_slug>[-\w]+)/environmentvariables/$',
        EnvironmentVariableList.as_view(),
        name='projects_environmentvariables',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/environmentvariables/create/$',
        EnvironmentVariableCreate.as_view(),
        name='projects_environmentvariables_create',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/environmentvariables/(?P<environmentvariable_pk>[-\w]+)/$',
        EnvironmentVariableDetail.as_view(),
        name='projects_environmentvariables_detail',
    ),
    url(
        r'^(?P<project_slug>[-\w]+)/environmentvariables/(?P<environmentvariable_pk>[-\w]+)/delete/$',  # noqa
        EnvironmentVariableDelete.as_view(),
        name='projects_environmentvariables_delete',
    ),
]

urlpatterns += environmentvariable_urls
