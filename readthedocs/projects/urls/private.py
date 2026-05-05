"""Project URLs for authenticated users."""

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.urls import re_path
from django.views.generic.base import RedirectView

from readthedocs.core.views import PageNotFoundView
from readthedocs.projects.backends.views import ImportWizardView
from readthedocs.projects.views import private
from readthedocs.projects.views.private import AddonsConfigUpdate
from readthedocs.projects.views.private import AutomationRuleCreate
from readthedocs.projects.views.private import AutomationRuleDelete
from readthedocs.projects.views.private import AutomationRuleList
from readthedocs.projects.views.private import AutomationRuleMove
from readthedocs.projects.views.private import AutomationRuleUpdate
from readthedocs.projects.views.private import DomainCreate
from readthedocs.projects.views.private import DomainDelete
from readthedocs.projects.views.private import DomainList
from readthedocs.projects.views.private import DomainUpdate
from readthedocs.projects.views.private import EnvironmentVariableCreate
from readthedocs.projects.views.private import EnvironmentVariableDelete
from readthedocs.projects.views.private import EnvironmentVariableList
from readthedocs.projects.views.private import ImportView
from readthedocs.projects.views.private import IntegrationCreate
from readthedocs.projects.views.private import IntegrationDelete
from readthedocs.projects.views.private import IntegrationDetail
from readthedocs.projects.views.private import IntegrationExchangeDetail
from readthedocs.projects.views.private import IntegrationList
from readthedocs.projects.views.private import IntegrationWebhookSync
from readthedocs.projects.views.private import ProjectAdvertisingUpdate
from readthedocs.projects.views.private import ProjectDashboard
from readthedocs.projects.views.private import ProjectDelete
from readthedocs.projects.views.private import ProjectEmailNotificationsCreate
from readthedocs.projects.views.private import ProjectNotifications
from readthedocs.projects.views.private import ProjectNotificationsDelete
from readthedocs.projects.views.private import ProjectPullRequestsUpdate
from readthedocs.projects.views.private import ProjectRedirectsCreate
from readthedocs.projects.views.private import ProjectRedirectsDelete
from readthedocs.projects.views.private import ProjectRedirectsInsert
from readthedocs.projects.views.private import ProjectRedirectsList
from readthedocs.projects.views.private import ProjectRedirectsUpdate
from readthedocs.projects.views.private import ProjectSearchSettingsUpdate
from readthedocs.projects.views.private import ProjectTranslationsCreate
from readthedocs.projects.views.private import ProjectTranslationsDelete
from readthedocs.projects.views.private import ProjectTranslationsList
from readthedocs.projects.views.private import ProjectUpdate
from readthedocs.projects.views.private import ProjectUsersCreate
from readthedocs.projects.views.private import ProjectUsersDelete
from readthedocs.projects.views.private import ProjectUsersList
from readthedocs.projects.views.private import ProjectVersionCreate
from readthedocs.projects.views.private import ProjectVersionDeleteHTML
from readthedocs.projects.views.private import ProjectVersionDetail
from readthedocs.projects.views.private import SearchAnalytics
from readthedocs.projects.views.private import TrafficAnalyticsView
from readthedocs.projects.views.private import WebHookCreate
from readthedocs.projects.views.private import WebHookDelete
from readthedocs.projects.views.private import WebHookExchangeDetail
from readthedocs.projects.views.private import WebHookList
from readthedocs.projects.views.private import WebHookUpdate


urlpatterns = [
    path("", ProjectDashboard.as_view(), name="projects_dashboard"),
    path(
        "import/",
        ImportView.as_view(wizard_class=ImportWizardView),
        {"wizard": ImportWizardView},
        name="projects_import",
    ),
    path(
        "import/manual/",
        ImportWizardView.as_view(),
        name="projects_import_manual",
    ),
    path(
        "<slug:project_slug>/",
        login_required(
            RedirectView.as_view(pattern_name="projects_detail", permanent=True),
        ),
        name="projects_manage",
    ),
    path(
        "<slug:project_slug>/edit/",
        ProjectUpdate.as_view(),
        name="projects_edit",
    ),
    path(
        "<slug:project_slug>/advanced/",
        login_required(
            RedirectView.as_view(pattern_name="projects_edit", permanent=True),
        ),
        name="projects_advanced",
    ),
    # NOTE: version_slug uses <str:> rather than <slug:> because VERSION_SLUG_REGEX
    # allows dots (e.g. "1.0", "3.2.1"), which Django's <slug:> converter
    # ([-a-zA-Z0-9_]+) does not match. The parameter is still named "version_slug"
    # to remain consistent with the rest of the codebase.
    path(
        "<slug:project_slug>/version/<str:version_slug>/delete_html/",
        ProjectVersionDeleteHTML.as_view(),
        name="project_version_delete_html",
    ),
    path(
        "<slug:project_slug>/version/<str:version_slug>/edit/",
        ProjectVersionDetail.as_view(),
        name="project_version_detail",
    ),
    path(
        "<slug:project_slug>/delete/",
        ProjectDelete.as_view(),
        name="projects_delete",
    ),
    path(
        "<slug:project_slug>/users/",
        ProjectUsersList.as_view(),
        name="projects_users",
    ),
    path(
        "<slug:project_slug>/users/create/",
        ProjectUsersCreate.as_view(),
        name="projects_users_create",
    ),
    path(
        "<slug:project_slug>/users/delete/",
        ProjectUsersDelete.as_view(),
        name="projects_users_delete",
    ),
    path(
        "<slug:project_slug>/notifications/",
        ProjectNotifications.as_view(),
        name="projects_notifications",
    ),
    path(
        "<slug:project_slug>/notifications/create/",
        ProjectEmailNotificationsCreate.as_view(),
        name="projects_notifications_create",
    ),
    path(
        "<slug:project_slug>/notifications/delete/",
        ProjectNotificationsDelete.as_view(),
        name="projects_notification_delete",
    ),
    path(
        "<slug:project_slug>/translations/",
        ProjectTranslationsList.as_view(),
        name="projects_translations",
    ),
    path(
        "<slug:project_slug>/translations/create/",
        ProjectTranslationsCreate.as_view(),
        name="projects_translations_create",
    ),
    path(
        "<slug:project_slug>/translations/delete/<slug:child_slug>/",
        ProjectTranslationsDelete.as_view(),
        name="projects_translations_delete",
    ),
    path(
        "<slug:project_slug>/redirects/",
        ProjectRedirectsList.as_view(),
        name="projects_redirects",
    ),
    path(
        "<slug:project_slug>/redirects/create/",
        ProjectRedirectsCreate.as_view(),
        name="projects_redirects_create",
    ),
    path(
        "<slug:project_slug>/redirects/<int:redirect_pk>/insert/<int:position>/",
        ProjectRedirectsInsert.as_view(),
        name="projects_redirects_insert",
    ),
    path(
        "<slug:project_slug>/redirects/<int:redirect_pk>/edit/",
        ProjectRedirectsUpdate.as_view(),
        name="projects_redirects_edit",
    ),
    path(
        "<slug:project_slug>/redirects/<int:redirect_pk>/delete/",
        ProjectRedirectsDelete.as_view(),
        name="projects_redirects_delete",
    ),
    path(
        "<slug:project_slug>/advertising/",
        ProjectAdvertisingUpdate.as_view(),
        name="projects_advertising",
    ),
    path(
        "<slug:project_slug>/pull-requests/",
        ProjectPullRequestsUpdate.as_view(),
        name="projects_pull_requests",
    ),
    path(
        "<slug:project_slug>/search-settings/",
        ProjectSearchSettingsUpdate.as_view(),
        name="projects_search_settings",
    ),
    path(
        "<slug:project_slug>/search-analytics/",
        SearchAnalytics.as_view(),
        name="projects_search_analytics",
    ),
    path(
        "<slug:project_slug>/traffic-analytics/",
        TrafficAnalyticsView.as_view(),
        name="projects_traffic_analytics",
    ),
    # Placeholder URLs, so that we can test the new templates
    # with organizations enabled from our community codebase.
    # TODO: migrate these functionalities from corporate to community.
    path(
        "<slug:project_slug>/sharing/",
        PageNotFoundView.as_view(),
        name="projects_temporary_access_list",
    ),
    path(
        "<slug:project_slug>/keys/",
        PageNotFoundView.as_view(),
        name="projects_keys",
    ),
    path(
        "<slug:project_slug>/version/create/",
        ProjectVersionCreate.as_view(),
        name="project_version_create",
    ),
]

domain_urls = [
    path(
        "<slug:project_slug>/domains/",
        DomainList.as_view(),
        name="projects_domains",
    ),
    path(
        "<slug:project_slug>/domains/create/",
        DomainCreate.as_view(),
        name="projects_domains_create",
    ),
    path(
        "<slug:project_slug>/domains/<int:domain_pk>/edit/",
        DomainUpdate.as_view(),
        name="projects_domains_edit",
    ),
    path(
        "<slug:project_slug>/domains/<int:domain_pk>/delete/",
        DomainDelete.as_view(),
        name="projects_domains_delete",
    ),
]

urlpatterns += domain_urls

addons_urls = [
    path(
        "<slug:project_slug>/addons/edit/",
        AddonsConfigUpdate.as_view(),
        name="projects_addons",
    ),
]

urlpatterns += addons_urls

integration_urls = [
    path(
        "<slug:project_slug>/integrations/",
        IntegrationList.as_view(),
        name="projects_integrations",
    ),
    path(
        "<slug:project_slug>/integrations/sync/",
        IntegrationWebhookSync.as_view(),
        name="projects_integrations_webhooks_sync",
    ),
    path(
        "<slug:project_slug>/integrations/create/",
        IntegrationCreate.as_view(),
        name="projects_integrations_create",
    ),
    path(
        "<slug:project_slug>/integrations/<int:integration_pk>/",
        IntegrationDetail.as_view(),
        name="projects_integrations_detail",
    ),
    path(
        "<slug:project_slug>/integrations/<int:integration_pk>/exchange/<slug:exchange_pk>/",
        IntegrationExchangeDetail.as_view(),
        name="projects_integrations_exchanges_detail",
    ),
    path(
        "<slug:project_slug>/integrations/<int:integration_pk>/sync/",
        IntegrationWebhookSync.as_view(),
        name="projects_integrations_webhooks_sync",
    ),
    path(
        "<slug:project_slug>/integrations/<int:integration_pk>/delete/",
        IntegrationDelete.as_view(),
        name="projects_integrations_delete",
    ),
]

urlpatterns += integration_urls

subproject_urls = [
    path(
        "<slug:project_slug>/subprojects/",
        private.ProjectRelationshipList.as_view(),
        name="projects_subprojects",
    ),
    path(
        "<slug:project_slug>/subprojects/create/",
        private.ProjectRelationshipCreate.as_view(),
        name="projects_subprojects_create",
    ),
    path(
        "<slug:project_slug>/subprojects/<slug:subproject_slug>/edit/",
        private.ProjectRelationshipUpdate.as_view(),
        name="projects_subprojects_update",
    ),
    path(
        "<slug:project_slug>/subprojects/<slug:subproject_slug>/delete/",
        private.ProjectRelationshipDelete.as_view(),
        name="projects_subprojects_delete",
    ),
]

urlpatterns += subproject_urls

environmentvariable_urls = [
    path(
        "<slug:project_slug>/environmentvariables/",
        EnvironmentVariableList.as_view(),
        name="projects_environmentvariables",
    ),
    path(
        "<slug:project_slug>/environmentvariables/create/",
        EnvironmentVariableCreate.as_view(),
        name="projects_environmentvariables_create",
    ),
    path(
        "<slug:project_slug>/environmentvariables/<int:environmentvariable_pk>/delete/",
        EnvironmentVariableDelete.as_view(),
        name="projects_environmentvariables_delete",
    ),
]

urlpatterns += environmentvariable_urls

automation_rule_urls = [
    path(
        "<slug:project_slug>/rules/",
        AutomationRuleList.as_view(),
        name="projects_automation_rule_list",
    ),
    # Keep as re_path because `steps` can be a negative integer (-?\d+),
    # which is not supported by Django's <int:> path converter.
    re_path(
        r"^(?P<project_slug>[-\w]+)/rules/(?P<automation_rule_pk>[-\w]+)/move/(?P<steps>-?\d+)/$",
        AutomationRuleMove.as_view(),
        name="projects_automation_rule_move",
    ),
    path(
        "<slug:project_slug>/rules/<int:automation_rule_pk>/delete/",
        AutomationRuleDelete.as_view(),
        name="projects_automation_rule_delete",
    ),
    path(
        "<slug:project_slug>/rules/create/",
        AutomationRuleCreate.as_view(),
        name="projects_automation_rule_create",
    ),
    path(
        "<slug:project_slug>/rules/<int:automation_rule_pk>/",
        AutomationRuleUpdate.as_view(),
        name="projects_automation_rule_edit",
    ),
]

urlpatterns += automation_rule_urls

webhook_urls = [
    path(
        "<slug:project_slug>/webhooks/",
        WebHookList.as_view(),
        name="projects_webhooks",
    ),
    path(
        "<slug:project_slug>/webhooks/create/",
        WebHookCreate.as_view(),
        name="projects_webhooks_create",
    ),
    path(
        "<slug:project_slug>/webhooks/<int:webhook_pk>/edit/",
        WebHookUpdate.as_view(),
        name="projects_webhooks_edit",
    ),
    path(
        "<slug:project_slug>/webhooks/<int:webhook_pk>/delete/",
        WebHookDelete.as_view(),
        name="projects_webhooks_delete",
    ),
    path(
        "<slug:project_slug>/webhooks/<int:webhook_pk>/exchanges/<slug:webhook_exchange_pk>/",
        WebHookExchangeDetail.as_view(),
        name="projects_webhooks_exchange",
    ),
]

urlpatterns += webhook_urls
