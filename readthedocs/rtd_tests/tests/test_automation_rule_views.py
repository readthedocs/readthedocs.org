import pytest
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    ALL_VERSIONS,
    ALL_VERSIONS_REGEX,
    BRANCH,
    SEMVER_VERSIONS,
    SEMVER_VERSIONS_REGEX,
    TAG,
)
from readthedocs.builds.models import VersionAutomationRule
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestAutomationRulesViews:

    @pytest.fixture(autouse=True)
    def setup(self, client, django_user_model):
        self.user = get(django_user_model)
        self.client = client
        self.client.force_login(self.user)

        self.project = get(Project, users=[self.user])

        self.list_rules_url = reverse(
            'projects_automation_rule_list', args=[self.project.slug],
        )

    def test_create_and_update_regex_rule(self):
        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'One rule',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        rule = self.project.automation_rules.get(description='One rule')
        assert rule.priority == 0

        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'Another rule',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': BRANCH,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        rule = self.project.automation_rules.get(description='Another rule')
        assert rule.priority == 1

        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_edit',
                args=[self.project.slug, rule.pk],
            ),
            {
                'description': 'Edit rule',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        rule.refresh_from_db()
        assert rule.description == 'Edit rule'
        assert rule.priority == 1

    def test_create_regex_rule_default_description(self):
        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        assert (
            self.project.automation_rules
            .filter(description='Activate version')
            .exists()
        )

    def test_create_regex_rule_custom_match(self):
        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'One rule',
                'match_arg': r'^master$',
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        rule = self.project.automation_rules.get(description='One rule')
        assert rule.match_arg == r'^master$'

    @pytest.mark.parametrize(
        'predefined_match_arg,expected_regex',
        [
            (ALL_VERSIONS, ALL_VERSIONS_REGEX),
            (SEMVER_VERSIONS, SEMVER_VERSIONS_REGEX),
        ],
    )
    def test_create_regex_rule_predefined_match(self, predefined_match_arg, expected_regex):
        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule',
                'predefined_match_arg': predefined_match_arg,
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        rule = self.project.automation_rules.get(description='rule')
        assert rule.get_match_arg() == expected_regex

    def test_empty_custom_match(self):
        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'One rule',
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        form = r.context['form']
        assert (
            'Custom match should not be empty.' in form.errors['match_arg']
        )

    def test_invalid_regex(self):
        r = self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'One rule',
                'match_arg': r'?$',
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        form = r.context['form']
        assert (
            'Invalid Python regular expression.' in form.errors['match_arg']
        )

    def test_delete_rule(self):
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-0',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-1',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': BRANCH,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-2',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': BRANCH,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        rule_0 = self.project.automation_rules.get(description='rule-0')
        rule_1 = self.project.automation_rules.get(description='rule-1')
        rule_2 = self.project.automation_rules.get(description='rule-2')

        self.project.automation_rules.all().count() == 3

        assert rule_0.priority == 0
        assert rule_1.priority == 1
        assert rule_2.priority == 2

        r = self.client.post(
            reverse(
                'projects_automation_rule_delete',
                args=[self.project.slug, rule_0.pk],
            ),
        )
        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        self.project.automation_rules.all().count() == 2

        rule_1.refresh_from_db()
        rule_2.refresh_from_db()

        assert rule_1.priority == 0
        assert rule_2.priority == 1

    def test_move_rule_up(self):
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-0',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-1',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': BRANCH,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-2',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': BRANCH,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        rule_0 = self.project.automation_rules.get(description='rule-0')
        rule_1 = self.project.automation_rules.get(description='rule-1')
        rule_2 = self.project.automation_rules.get(description='rule-2')

        r = self.client.post(
            reverse(
                'projects_automation_rule_move',
                args=[self.project.slug, rule_1.pk, -1],
            ),
        )
        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        rule_0.refresh_from_db()
        rule_1.refresh_from_db()
        rule_2.refresh_from_db()

        assert rule_1.priority == 0
        assert rule_0.priority == 1
        assert rule_2.priority == 2

    def test_move_rule_down(self):
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-0',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': TAG,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-1',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': BRANCH,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )
        self.client.post(
            reverse(
                'projects_automation_rule_regex_create',
                args=[self.project.slug],
            ),
            {
                'description': 'rule-2',
                'predefined_match_arg': ALL_VERSIONS,
                'version_type': BRANCH,
                'action': VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            },
        )

        rule_0 = self.project.automation_rules.get(description='rule-0')
        rule_1 = self.project.automation_rules.get(description='rule-1')
        rule_2 = self.project.automation_rules.get(description='rule-2')

        r = self.client.post(
            reverse(
                'projects_automation_rule_move',
                args=[self.project.slug, rule_1.pk, 1],
            ),
        )
        assert r.status_code == 302
        assert r['Location'] == self.list_rules_url

        rule_0.refresh_from_db()
        rule_1.refresh_from_db()
        rule_2.refresh_from_db()

        assert rule_0.priority == 0
        assert rule_2.priority == 1
        assert rule_1.priority == 2
