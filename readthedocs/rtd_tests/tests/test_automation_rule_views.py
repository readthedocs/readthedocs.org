import pytest
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    ALL_VERSIONS,
    BRANCH,
    CUSTOM_MATCH,
    TAG,
)
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import AutomationRule, Project


@pytest.mark.django_db
class TestAutomationRulesViews:
    @pytest.fixture(autouse=True)
    def setup(self, client, django_user_model, settings):
        settings.RTD_ALLOW_ORGANIZATIONS = False

        self.user = get(django_user_model)
        self.client = client
        self.client.force_login(self.user)

        self.project = get(Project, users=[self.user])

        self.list_rules_url = reverse(
            "projects_automation_rule_list",
            args=[self.project.slug],
        )

    def test_create_and_update_rule(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "One rule",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.get(description="One rule")
        assert rule.priority == 0

        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Another rule",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.get(description="Another rule")
        assert rule.priority == 0

        r = self.client.post(
            reverse(
                "projects_automation_rule_edit",
                args=[self.project.slug, rule.pk],
            ),
            {
                "description": "Edit rule",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule.refresh_from_db()
        assert rule.description == "Edit rule"
        assert rule.priority == 0

    def test_create_rule_default_description(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.first()
        assert rule.description is None
        assert rule.get_description() == "Activate version"

    def test_create_rule_custom_match(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "One rule",
                "version_predefined_match_pattern": CUSTOM_MATCH,
                "version_match_pattern": r"^master$",
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.get(description="One rule")
        assert rule.version_predefined_match_pattern == CUSTOM_MATCH
        assert rule.version_match_pattern == r"^master$"

    def test_create_rule_predefined_match(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.get(description="rule")
        assert rule.version_predefined_match_pattern == ALL_VERSIONS

    def test_create_rule_with_webhook_files_filter(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Webhook rule",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.TRIGGER_BUILD_ACTION,
                "webhook_files_match_pattern": "docs/*.rst\nrequirements.txt",
            },
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.get(description="Webhook rule")
        assert "docs/*.rst" in rule.webhook_files_match_pattern
        assert "requirements.txt" in rule.webhook_files_match_pattern

    def test_create_rule_invalid_regex_version_match(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Bad regex rule",
                "version_predefined_match_pattern": CUSTOM_MATCH,
                "version_match_pattern": "[invalid",
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 200
        assert self.project.automation_rules.count() == 0

    def test_create_rule_custom_match_empty_pattern(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Empty custom match",
                "version_predefined_match_pattern": CUSTOM_MATCH,
                "version_match_pattern": "",
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 200
        assert self.project.automation_rules.count() == 0

    def test_create_rule_with_webhook_labels_filter(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Label rule",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.TRIGGER_BUILD_ACTION,
                "webhook_labels_match_pattern": "docs|build",
            },
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.get(description="Label rule")
        assert rule.webhook_labels_match_pattern == "docs|build"

    def test_create_rule_invalid_regex_labels(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Bad label regex",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.TRIGGER_BUILD_ACTION,
                "webhook_labels_match_pattern": "[invalid",
            },
        )
        assert r.status_code == 200
        assert self.project.automation_rules.count() == 0

    def test_create_rule_with_webhook_commit_message_filter(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Commit message rule",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.TRIGGER_BUILD_ACTION,
                "webhook_commit_message_match_pattern": "^fix|feature",
            },
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule = self.project.automation_rules.get(description="Commit message rule")
        assert rule.webhook_commit_message_match_pattern == "^fix|feature"

    def test_create_rule_invalid_regex_commit_message(self):
        r = self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "Bad commit regex",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.TRIGGER_BUILD_ACTION,
                "webhook_commit_message_match_pattern": "[invalid",
            },
        )
        assert r.status_code == 200
        assert self.project.automation_rules.count() == 0

    def test_delete_rule(self):
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-2",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-1",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-0",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        rule_0 = self.project.automation_rules.get(description="rule-0")
        rule_1 = self.project.automation_rules.get(description="rule-1")
        rule_2 = self.project.automation_rules.get(description="rule-2")

        assert self.project.automation_rules.all().count() == 3

        assert rule_0.priority == 0
        assert rule_1.priority == 1
        assert rule_2.priority == 2

        r = self.client.post(
            reverse(
                "projects_automation_rule_delete",
                args=[self.project.slug, rule_0.pk],
            ),
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        assert self.project.automation_rules.all().count() == 2

        rule_1.refresh_from_db()
        rule_2.refresh_from_db()

        assert rule_1.priority == 0
        assert rule_2.priority == 1

    def test_move_rule_up(self):
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-2",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-1",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-0",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        rule_0 = self.project.automation_rules.get(description="rule-0")
        rule_1 = self.project.automation_rules.get(description="rule-1")
        rule_2 = self.project.automation_rules.get(description="rule-2")

        r = self.client.post(
            reverse(
                "projects_automation_rule_move",
                args=[self.project.slug, rule_1.pk, -1],
            ),
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule_0.refresh_from_db()
        rule_1.refresh_from_db()
        rule_2.refresh_from_db()

        assert rule_1.priority == 0
        assert rule_0.priority == 1
        assert rule_2.priority == 2

    def test_move_rule_down(self):
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-2",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [TAG],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-1",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                "projects_automation_rule_create",
                args=[self.project.slug],
            ),
            {
                "description": "rule-0",
                "version_predefined_match_pattern": ALL_VERSIONS,
                "version_types": [BRANCH],
                "action": AutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        rule_0 = self.project.automation_rules.get(description="rule-0")
        rule_1 = self.project.automation_rules.get(description="rule-1")
        rule_2 = self.project.automation_rules.get(description="rule-2")

        r = self.client.post(
            reverse(
                "projects_automation_rule_move",
                args=[self.project.slug, rule_1.pk, 1],
            ),
        )
        assert r.status_code == 302
        assert r["Location"] == self.list_rules_url

        rule_0.refresh_from_db()
        rule_1.refresh_from_db()
        rule_2.refresh_from_db()

        assert rule_0.priority == 0
        assert rule_2.priority == 1
        assert rule_1.priority == 2


class TestAutomationRulesViewsWithOrganizations(TestAutomationRulesViews):
    @pytest.fixture(autouse=True)
    def setup_organization(self, settings):
        settings.RTD_ALLOW_ORGANIZATIONS = True
        self.organization = get(
            Organization,
            owners=[self.user],
            projects=[self.project],
        )
