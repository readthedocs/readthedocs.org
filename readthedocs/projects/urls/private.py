"""Project URLs for authenticated users."""

from django.conf import settings
from django.conf.urls import re_path
from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView

from readthedocs.constants import pattern_opts
from readthedocs.projects.backends.views import ImportWizardView
from readthedocs.projects.views import private
from readthedocs.projects.views.private import (
    AutomationRuleDelete,
    AutomationRuleList,
    AutomationRuleMove,
    DomainCreate,
    DomainDelete,
    DomainList,
    DomainUpdate,
    EnvironmentVariableCreate,
    EnvironmentVariableDelete,
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
    ProjectNotifications,
    ProjectNotificationsDelete,
    ProjectRedirects,
    ProjectRedirectsDelete,
    ProjectTranslationsDelete,
    ProjectTranslationsListAndCreate,
    ProjectUpdate,
    ProjectUsersCreateList,
    ProjectUsersDelete,
    ProjectVersionCreate,
    ProjectVersionDeleteHTML,
    ProjectVersionDetail,
    RegexAutomationRuleCreate,
    RegexAutomationRuleUpdate,
    SearchAnalytics,
    TrafficAnalyticsView,
    WebHookCreate,
    WebHookDelete,
    WebHookExchangeDetail,
    WebHookList,
    WebHookUpdate,
)

urlpatterns = [
    re_path(r'^$', ProjectDashboard.as_view(), name='projects_dashboard'),
    re_path(
        r'^import/$', ImportView.as_view(wizard_class=ImportWizardView),
        {'wizard': ImportWizardView}, name='projects_import',
    ),
    re_path(
        r'^import/manual/$', ImportWizardView.as_view(),
        name='projects_import_manual',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/$',
        login_required(
            RedirectView.as_view(pattern_name='projects_detail', permanent=True),
        ),
        name='projects_manage',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/edit/$', ProjectUpdate.as_view(),
        name='projects_edit',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/advanced/$',
        ProjectAdvancedUpdate.as_view(), name='projects_advanced',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[^/]+)/delete_html/$',
        ProjectVersionDeleteHTML.as_view(),
        name='project_version_delete_html',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/version/(?P<version_slug>[^/]+)/edit/$',
        ProjectVersionDetail.as_view(),
        name='project_version_detail',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/delete/$',
        ProjectDelete.as_view(),
        name='projects_delete',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/users/$',
        ProjectUsersCreateList.as_view(),
        name='projects_users',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/users/delete/$',
        ProjectUsersDelete.as_view(),
        name='projects_users_delete',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/notifications/$',
        ProjectNotifications.as_view(),
        name='projects_notifications',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/notifications/delete/$',
        ProjectNotificationsDelete.as_view(),
        name='projects_notification_delete',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/translations/$',
        ProjectTranslationsListAndCreate.as_view(),
        name='projects_translations',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/translations/delete/(?P<child_slug>[-\w]+)/$',  # noqa
        ProjectTranslationsDelete.as_view(),
        name='projects_translations_delete',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/redirects/$',
        ProjectRedirects.as_view(),
        name='projects_redirects',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/redirects/delete/$',
        ProjectRedirectsDelete.as_view(),
        name='projects_redirects_delete',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/advertising/$',
        ProjectAdvertisingUpdate.as_view(), name='projects_advertising',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/search-analytics/$',
        SearchAnalytics.as_view(),
        name='projects_search_analytics',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/traffic-analytics/$',
        TrafficAnalyticsView.as_view(), name='projects_traffic_analytics',
    ),
]

# TODO move this up to the list above when it's not a conditional URL.
# Currently, this is only used by the new theme, we don't allow for "create" in
# our current templates.
if settings.RTD_EXT_THEME_ENABLED:
    urlpatterns.append(
        re_path(
            r'^(?P<project_slug>[-\w]+)/version/create/$',
            ProjectVersionCreate.as_view(),
            name='project_version_create',
        ),
    )

domain_urls = [
    re_path(
        r'^(?P<project_slug>[-\w]+)/domains/$',
        DomainList.as_view(),
        name='projects_domains',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/domains/create/$',
        DomainCreate.as_view(),
        name='projects_domains_create',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/domains/(?P<domain_pk>[-\w]+)/edit/$',
        DomainUpdate.as_view(),
        name='projects_domains_edit',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/domains/(?P<domain_pk>[-\w]+)/delete/$',
        DomainDelete.as_view(),
        name='projects_domains_delete',
    ),
]

urlpatterns += domain_urls

integration_urls = [
    re_path(
        r'^(?P<project_slug>{project_slug})/integrations/$'.format(
            **pattern_opts
        ),
        IntegrationList.as_view(),
        name='projects_integrations',
    ),
    re_path(
        r'^(?P<project_slug>{project_slug})/integrations/sync/$'.format(
            **pattern_opts
        ),
        IntegrationWebhookSync.as_view(),
        name='projects_integrations_webhooks_sync',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/integrations/create/$'.format(
                **pattern_opts
            )
        ),
        IntegrationCreate.as_view(),
        name='projects_integrations_create',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'integrations/(?P<integration_pk>{integer_pk})/$'.format(
                **pattern_opts
            )
        ),
        IntegrationDetail.as_view(),
        name='projects_integrations_detail',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'integrations/(?P<integration_pk>{integer_pk})/'
            r'exchange/(?P<exchange_pk>[-\w]+)/$'.format(**pattern_opts)
        ),
        IntegrationExchangeDetail.as_view(),
        name='projects_integrations_exchanges_detail',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'integrations/(?P<integration_pk>{integer_pk})/sync/$'.format(
                **pattern_opts
            )
        ),
        IntegrationWebhookSync.as_view(),
        name='projects_integrations_webhooks_sync',
    ),
    re_path(
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
    re_path(
        r'^(?P<project_slug>{project_slug})/subprojects/$'.format(
            **pattern_opts
        ),
        private.ProjectRelationshipList.as_view(),
        name='projects_subprojects',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/subprojects/create/$'.format(
                **pattern_opts
            )
        ),
        private.ProjectRelationshipCreate.as_view(),
        name='projects_subprojects_create',
    ),
    re_path(
        (
            r'^(?P<project_slug>{project_slug})/'
            r'subprojects/(?P<subproject_slug>{project_slug})/edit/$'.format(
                **pattern_opts
            )
        ),
        private.ProjectRelationshipUpdate.as_view(),
        name='projects_subprojects_update',
    ),
    re_path(
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
    re_path(
        r'^(?P<project_slug>[-\w]+)/environmentvariables/$',
        EnvironmentVariableList.as_view(),
        name='projects_environmentvariables',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/environmentvariables/create/$',
        EnvironmentVariableCreate.as_view(),
        name='projects_environmentvariables_create',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/environmentvariables/(?P<environmentvariable_pk>[-\w]+)/delete/$',  # noqa
        EnvironmentVariableDelete.as_view(),
        name='projects_environmentvariables_delete',
    ),
]

urlpatterns += environmentvariable_urls

automation_rule_urls = [
    re_path(
        r'^(?P<project_slug>[-\w]+)/rules/$',
        AutomationRuleList.as_view(),
        name='projects_automation_rule_list',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/rules/(?P<automation_rule_pk>[-\w]+)/move/(?P<steps>-?\d+)/$',
        AutomationRuleMove.as_view(),
        name='projects_automation_rule_move',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/rules/(?P<automation_rule_pk>[-\w]+)/delete/$',
        AutomationRuleDelete.as_view(),
        name='projects_automation_rule_delete',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/rules/regex/create/$',
        RegexAutomationRuleCreate.as_view(),
        name='projects_automation_rule_regex_create',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/rules/regex/(?P<automation_rule_pk>[-\w]+)/$',
        RegexAutomationRuleUpdate.as_view(),
        name='projects_automation_rule_regex_edit',
    ),
]

urlpatterns += automation_rule_urls

webhook_urls = [
    re_path(
        r'^(?P<project_slug>[-\w]+)/webhooks/$',
        WebHookList.as_view(),
        name='projects_webhooks',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/webhooks/create/$',
        WebHookCreate.as_view(),
        name='projects_webhooks_create',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/webhooks/(?P<webhook_pk>[-\w]+)/edit/$',
        WebHookUpdate.as_view(),
        name='projects_webhooks_edit',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/webhooks/(?P<webhook_pk>[-\w]+)/delete/$',
        WebHookDelete.as_view(),
        name='projects_webhooks_delete',
    ),
    re_path(
        r'^(?P<project_slug>[-\w]+)/webhooks/(?P<webhook_pk>[-\w]+)/exchanges/(?P<webhook_exchange_pk>[-\w]+)/$',  # noqa
        WebHookExchangeDetail.as_view(),
        name='projects_webhooks_exchange',
    ),
]

urlpatterns += webhook_urls
