from unittest import mock

import pytest
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    ALL_VERSIONS,
    BRANCH,
    CUSTOM_MATCH,
    EXTERNAL,
    LATEST,
    SEMVER_VERSIONS,
    TAG,
)
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import AutomationRule, Project


@pytest.mark.django_db
@mock.patch("readthedocs.builds.automation_actions.trigger_build")
class TestAutomationRuleVersionMatching:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.project = get(Project)

    @pytest.mark.parametrize(
        "version_name,regex,result",
        [
            # Matches all
            ("master", r".*", True),
            ("latest", r".*", True),
            # Contains match
            ("master", r"master", True),
            ("master-something", r"master", True),
            ("something-master", r"master", True),
            ("foo", r"master", False),
            # Starts with match
            ("master", r"^master", True),
            ("master-foo", r"^master", True),
            ("foo-master", r"^master", False),
            # Ends with match
            ("master", r"master$", True),
            ("foo-master", r"master$", True),
            ("master-foo", r"master$", False),
            # Exact match
            ("master", r"^master$", True),
            ("masterr", r"^master$", False),
            ("mmaster", r"^master$", False),
            # Match versions from 1.3.x series
            ("1.3.2", r"^1\.3\..*", True),
            ("1.3.3.5", r"^1\.3\..*", True),
            ("1.3.3-rc", r"^1\.3\..*", True),
            ("1.2.3", r"^1\.3\..*", False),
            # Some special regex scape characters
            ("12-a", r"^\d{2}-\D$", True),
            ("1-a", r"^\d{2}-\D$", False),
            # Groups
            ("1.3-rc", r"^(\d\.?)*-(\w*)$", True),
            # Bad regex
            ("master", r"*", False),
            ("master", r"?", False),
        ],
    )
    @pytest.mark.parametrize("version_type", [BRANCH, TAG])
    def test_match(
        self,
        trigger_build,
        version_name,
        regex,
        result,
        version_type,
    ):
        version = get(
            Version,
            verbose_name=version_name,
            project=self.project,
            active=False,
            type=version_type,
            built=False,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=CUSTOM_MATCH,
            version_match_pattern=regex,
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
            version_types=[version_type],
        )
        assert rule.match_version(version) is result
        if result:
            assert rule.run(version) is True
            assert rule.matches.all().count() == 1
        else:
            assert rule.matches.all().count() == 0

    @pytest.mark.parametrize(
        "version_name,result",
        [
            ("master", True),
            ("latest", True),
            ("master-something", True),
            ("something-master", True),
            ("1.3.2", True),
            ("1.3.3.5", True),
            ("1.3.3-rc", True),
            ("12-a", True),
            ("1-a", True),
        ],
    )
    @pytest.mark.parametrize("version_type", [BRANCH, TAG])
    def test_predefined_match_all_versions(
        self, trigger_build, version_name, result, version_type
    ):
        version = get(
            Version,
            verbose_name=version_name,
            project=self.project,
            active=False,
            type=version_type,
            built=False,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
            version_types=[version_type],
        )
        assert rule.match_version(version) is result
        if result:
            assert rule.run(version) is True

    @pytest.mark.parametrize(
        "version_name,result",
        [
            ("master", False),
            ("latest", False),
            ("master-something", False),
            ("something-master", False),
            ("1.3.3.5", False),
            ("12-a", False),
            ("1-a", False),
            ("1.3.2", True),
            ("1.3.3-rc", True),
            ("0.1.1", True),
        ],
    )
    @pytest.mark.parametrize("version_type", [BRANCH, TAG])
    def test_predefined_match_semver_versions(
        self, trigger_build, version_name, result, version_type
    ):
        version = get(
            Version,
            verbose_name=version_name,
            project=self.project,
            active=False,
            type=version_type,
            built=False,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=SEMVER_VERSIONS,
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
            version_types=[version_type],
        )
        # Test match() and run() separately following new pattern
        assert rule.match_version(version) is result
        if result:
            assert rule.run(version) is True

    def test_action_activation(self, trigger_build):
        version = get(
            Version,
            verbose_name="v2",
            project=self.project,
            active=False,
            type=TAG,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
            version_types=[TAG],
        )
        assert rule.run(version) is True
        assert version.active is True
        trigger_build.assert_called_once()

    @pytest.mark.parametrize("version_type", [BRANCH, TAG])
    def test_action_delete_version(self, trigger_build, version_type):
        slug = "delete-me"
        version = get(
            Version,
            slug=slug,
            verbose_name=slug,
            project=self.project,
            active=True,
            type=version_type,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.DELETE_VERSION_ACTION,
            version_types=[version_type],
        )
        assert rule.run(version) is True
        assert not self.project.versions.filter(slug=slug).exists()

    @pytest.mark.parametrize("version_type", [BRANCH, TAG])
    def test_action_delete_version_on_default_version(
        self, trigger_build, version_type
    ):
        slug = "delete-me"
        version = get(
            Version,
            slug=slug,
            verbose_name=slug,
            project=self.project,
            active=True,
            type=version_type,
        )
        self.project.default_version = slug
        self.project.save()

        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.DELETE_VERSION_ACTION,
            version_types=[version_type],
        )
        assert rule.run(version) is True
        assert self.project.versions.filter(slug=slug).exists()

    def test_action_set_default_version(self, trigger_build):
        version = get(
            Version,
            verbose_name="v2",
            project=self.project,
            active=True,
            type=TAG,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.SET_DEFAULT_VERSION_ACTION,
            version_types=[TAG],
        )
        assert self.project.get_default_version() == LATEST
        assert rule.run(version) is True
        assert self.project.get_default_version() == version.slug

    def test_version_hide_action(self, trigger_build):
        version = get(
            Version,
            verbose_name="v2",
            project=self.project,
            active=False,
            hidden=False,
            type=TAG,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.HIDE_VERSION_ACTION,
            version_types=[TAG],
        )
        assert rule.run(version) is True
        assert version.active is True
        assert version.hidden is True
        trigger_build.assert_called_once()

    def test_version_make_public_action(self, trigger_build):
        version = get(
            Version,
            verbose_name="v2",
            project=self.project,
            active=False,
            hidden=False,
            type=TAG,
            privacy_level=PRIVATE,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.MAKE_VERSION_PUBLIC_ACTION,
            version_types=[TAG],
        )
        assert rule.run(version) is True
        assert version.privacy_level == PUBLIC
        trigger_build.assert_not_called()

    def test_version_make_private_action(self, trigger_build):
        version = get(
            Version,
            verbose_name="v2",
            project=self.project,
            active=False,
            hidden=False,
            type=TAG,
            privacy_level=PUBLIC,
        )
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.MAKE_VERSION_PRIVATE_ACTION,
            version_types=[TAG],
        )
        assert rule.run(version) is True
        assert version.privacy_level == PRIVATE
        trigger_build.assert_not_called()

    def test_matches_history(self, trigger_build):
        version = get(
            Version,
            verbose_name="test",
            project=self.project,
            active=False,
            type=TAG,
            built=False,
        )

        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=CUSTOM_MATCH,
            version_match_pattern="^test",
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
            version_types=[TAG],
        )

        assert rule.run(version) is True
        assert rule.matches.all().count() == 1

        match = rule.matches.first()
        assert match.version_name == "test"
        assert match.version_type == TAG
        assert match.action == AutomationRule.ACTIVATE_VERSION_ACTION
        assert match.match_arg == "^test"

        for i in range(1, 31):
            version.verbose_name = f"test {i}"
            version.save()
            assert rule.run(version) is True

        assert rule.matches.all().count() == 15

        match = rule.matches.first()
        assert match.version_name == "test 30"
        assert match.version_type == TAG
        assert match.action == AutomationRule.ACTIVATE_VERSION_ACTION
        assert match.match_arg == "^test"

        match = rule.matches.last()
        assert match.version_name == "test 16"
        assert match.version_type == TAG
        assert match.action == AutomationRule.ACTIVATE_VERSION_ACTION
        assert match.match_arg == "^test"


@pytest.mark.django_db
class TestAutomationRuleManager:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.project = get(Project)

    def test_add_rule(self):
        assert not self.project.automation_rules.all()

        rule = AutomationRule.objects.create(
            project=self.project,
            description="First rule",
            version_predefined_match_pattern=ALL_VERSIONS,
            version_types=[TAG],
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
        )

        # First rule gets added with priority 0
        assert self.project.automation_rules.count() == 1
        assert rule.priority == 0

        # Adding a second rule
        rule = AutomationRule.objects.create(
            project=self.project,
            description="Second rule",
            version_predefined_match_pattern=ALL_VERSIONS,
            version_types=[BRANCH],
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
        )
        assert self.project.automation_rules.count() == 2
        assert rule.priority == 0

        # Adding a rule with a not sequential priority
        rule = get(
            AutomationRule,
            description="Third rule",
            project=self.project,
            priority=9,
            version_predefined_match_pattern=ALL_VERSIONS,
            version_types=[TAG],
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
        )
        assert self.project.automation_rules.count() == 3
        assert rule.priority == 2

        # Adding a new rule
        rule = AutomationRule.objects.create(
            project=self.project,
            description="Fourth rule",
            version_predefined_match_pattern=ALL_VERSIONS,
            version_types=[BRANCH],
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
        )
        assert self.project.automation_rules.count() == 4
        assert rule.priority == 0

        assert list(
            self.project.automation_rules.all().values_list("priority", flat=True)
        ) == [0, 1, 2, 3]


@pytest.mark.django_db
class TestAutomationRuleMove:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.project = get(Project)
        self.rule_5 = self._add_rule("Five")
        self.rule_4 = self._add_rule("Four")
        self.rule_3 = self._add_rule("Three")
        self.rule_2 = self._add_rule("Two")
        self.rule_1 = self._add_rule("One")
        self.rule_0 = self._add_rule("Zero")
        self._refresh_rules()
        assert self.project.automation_rules.count() == 6

    def _add_rule(self, description):
        rule = AutomationRule.objects.create(
            project=self.project,
            description=description,
            version_predefined_match_pattern=ALL_VERSIONS,
            version_types=[BRANCH],
            action=AutomationRule.ACTIVATE_VERSION_ACTION,
        )
        return rule

    def test_move_rule_one_step(self):
        self.rule_0.move(1)
        new_order = [
            self.rule_1,
            self.rule_0,
            self.rule_2,
            self.rule_3,
            self.rule_4,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rule_positive_steps(self):
        self.rule_1.move(1)
        self.rule_1.move(2)

        new_order = [
            self.rule_0,
            self.rule_2,
            self.rule_3,
            self.rule_4,
            self.rule_1,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rule_positive_steps_overflow(self):
        self.rule_2.move(3)
        self.rule_2.move(2)

        new_order = [
            self.rule_0,
            self.rule_2,
            self.rule_1,
            self.rule_3,
            self.rule_4,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rules_positive_steps(self):
        self.rule_2.move(2)
        self.rule_0.refresh_from_db()
        self.rule_0.move(7)
        self.rule_4.refresh_from_db()
        self.rule_4.move(4)
        self.rule_1.refresh_from_db()
        self.rule_1.move(1)

        new_order = [
            self.rule_4,
            self.rule_1,
            self.rule_0,
            self.rule_3,
            self.rule_2,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rule_one_negative_step(self):
        self.rule_3.move(-1)
        new_order = [
            self.rule_0,
            self.rule_1,
            self.rule_3,
            self.rule_2,
            self.rule_4,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rule_negative_steps(self):
        self.rule_4.move(-1)
        self.rule_4.move(-2)

        new_order = [
            self.rule_0,
            self.rule_4,
            self.rule_1,
            self.rule_2,
            self.rule_3,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rule_negative_steps_overflow(self):
        self.rule_2.move(-3)
        self.rule_2.move(-2)

        new_order = [
            self.rule_0,
            self.rule_1,
            self.rule_3,
            self.rule_2,
            self.rule_4,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rules_negative_steps(self):
        self.rule_2.move(-2)
        self.rule_5.refresh_from_db()
        self.rule_5.move(-7)
        self.rule_3.refresh_from_db()
        self.rule_3.move(-2)
        self.rule_1.refresh_from_db()
        self.rule_1.move(-1)

        new_order = [
            self.rule_2,
            self.rule_3,
            self.rule_1,
            self.rule_0,
            self.rule_5,
            self.rule_4,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_move_rules_up_and_down(self):
        self.rule_2.move(2)
        self.rule_5.refresh_from_db()
        self.rule_5.move(-3)
        self.rule_3.refresh_from_db()
        self.rule_3.move(4)
        self.rule_1.refresh_from_db()
        self.rule_1.move(-1)

        new_order = [
            self.rule_0,
            self.rule_1,
            self.rule_3,
            self.rule_5,
            self.rule_4,
            self.rule_2,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_delete_fist_rule(self):
        self.rule_0.delete()
        assert self.project.automation_rules.all().count() == 5

        new_order = [
            self.rule_1,
            self.rule_2,
            self.rule_3,
            self.rule_4,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_delete_last_rule(self):
        self.rule_5.delete()
        assert self.project.automation_rules.all().count() == 5

        new_order = [
            self.rule_0,
            self.rule_1,
            self.rule_2,
            self.rule_3,
            self.rule_4,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def test_delete_some_rule(self):
        self.rule_2.delete()
        assert self.project.automation_rules.all().count() == 5

        new_order = [
            self.rule_0,
            self.rule_1,
            self.rule_3,
            self.rule_4,
            self.rule_5,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority

    def _refresh_rules(self):
        rules = [
            self.rule_0,
            self.rule_1,
            self.rule_2,
            self.rule_3,
            self.rule_4,
            self.rule_5,
        ]
        for rule in rules:
            if rule.pk:
                rule.refresh_from_db()

    def test_delete_some_rules(self):
        self.rule_2.delete()
        self._refresh_rules()
        self.rule_0.delete()
        self._refresh_rules()
        self.rule_5.delete()
        self._refresh_rules()

        assert self.project.automation_rules.all().count() == 3

        new_order = [
            self.rule_1,
            self.rule_3,
            self.rule_4,
        ]

        for priority, rule in enumerate(self.project.automation_rules.all()):
            assert rule == new_order[priority]
            assert rule.priority == priority


@pytest.mark.django_db
@mock.patch("readthedocs.builds.automation_actions.trigger_build")
class TestWebhookAutomationRules:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.project = get(Project)
        self.version = get(
            Version,
            verbose_name="main",
            project=self.project,
            active=True,
            type=BRANCH,
        )

    @pytest.mark.parametrize(
        "pattern,files,should_match",
        [
            # Exact match
            ("docs/index.rst", ["docs/index.rst"], True),
            ("docs/index.rst", ["docs/other.rst"], False),
            # Wildcard matches - NOTE: fnmatch * matches across / unlike shell globs
            ("*.py", ["test.py"], True),
            ("*.py", ["src/test.py"], True),  # * matches everything including /
            ("*.py", ["test.txt"], False),
            # Recursive wildcard - ** is just two * wildcards in fnmatch
            ("**/*.py", ["test.py"], False),  # literal ** needs dir before *.py
            ("**/*.py", ["src/test.py"], True),
            ("**/*.py", ["src/deep/test.py"], True),
            ("**/*.py", ["test.txt"], False),
            # Directory patterns
            ("docs/*", ["docs/index.rst"], True),
            ("docs/*", ["docs/subdir/index.rst"], True),  # * matches across /
            ("docs/**", ["docs/index.rst"], True),
            ("docs/**", ["docs/subdir/index.rst"], True),
            ("docs/**", ["src/index.rst"], False),
            # Mixed patterns
            ("docs/*.rst", ["docs/index.rst"], True),
            ("docs/*.rst", ["docs/api.rst"], True),
            ("docs/*.rst", ["docs/index.md"], False),
            ("docs/*.rst", ["docs/subdir/index.rst"], True),  # * matches across /
            # Question mark wildcard
            ("file?.txt", ["file1.txt"], True),
            ("file?.txt", ["file2.txt"], True),
            ("file?.txt", ["file10.txt"], False),
            # Character ranges
            ("file[0-9].txt", ["file5.txt"], True),
            ("file[0-9].txt", ["filea.txt"], False),
        ],
    )
    def test_match_files(self, trigger_build, pattern, files, should_match):
        """Test that AutomationRule.match_webhook() correctly matches file patterns."""
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            webhook_files_match_pattern=[pattern],
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[BRANCH],
        )
        assert rule.match_webhook(changed_files=files) is should_match

    def test_match_multiple_files(self, trigger_build):
        """Test that match returns True if any file in the list matches."""
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            webhook_files_match_pattern=["docs/*.rst"],
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[BRANCH],
        )

        # Should match if any file matches
        assert (
            rule.match_webhook(
                changed_files=["src/code.py", "docs/index.rst", "README.md"]
            )
            is True
        )

        # Should not match if no files match
        assert rule.match_webhook(changed_files=["src/code.py", "README.md"]) is False

    def test_match_empty_file_list(self, trigger_build):
        """Test that match returns False for empty file list."""
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            webhook_files_match_pattern=["docs/*.rst"],
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[BRANCH],
        )
        assert rule.match_webhook(changed_files=[]) is False

    def test_match_no_webhook_filter_always_passes(self, trigger_build):
        """Test that match_webhook returns True when no filters are configured."""
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            webhook_files_match_pattern=None,
            webhook_labels_match_pattern=None,
            webhook_commit_message_match_pattern=None,
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[BRANCH],
        )
        # When no webhook filters are set, match_webhook should always return True
        assert rule.match_webhook(changed_files=[]) is True
        assert rule.match_webhook(changed_files=["any/file.py"]) is True

    def test_run_triggers_build_for_active_version(self, trigger_build):
        """Test that run() triggers a build for an active version."""
        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            webhook_files_match_pattern=["docs/*.rst"],
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[BRANCH],
        )

        result = rule.run(self.version)
        assert result is True
        trigger_build.assert_called_once_with(
            project=self.project,
            version=self.version,
            from_webhook=True,
        )

    def test_run_does_not_trigger_build_for_inactive_version(self, trigger_build):
        """Test that run() does not trigger a build for an inactive version."""
        self.version.active = False
        self.version.save()

        rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            webhook_files_match_pattern=["docs/*.rst"],
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[BRANCH],
        )

        result = rule.run(self.version)
        assert result is True
        trigger_build.assert_not_called()

    def test_version_type_filtering(self, trigger_build):
        """Test that rules only apply to matching version types."""
        branch_rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[BRANCH],
        )

        # Create a tag version
        tag_version = get(
            Version,
            verbose_name="v1.0",
            project=self.project,
            active=True,
            type=TAG,
        )

        # Branch version should match version type
        assert branch_rule.match_version(self.version) is True
        # Tag version should not match (wrong type)
        assert branch_rule.match_version(tag_version) is False

    def test_external_version_support(self, trigger_build):
        """Test that AutomationRule works with external versions (PRs)."""
        external_rule = get(
            AutomationRule,
            project=self.project,
            priority=0,
            version_predefined_match_pattern=ALL_VERSIONS,
            webhook_files_match_pattern=["docs/**"],
            action=AutomationRule.TRIGGER_BUILD_ACTION,
            version_types=[EXTERNAL],
        )

        external_version = get(
            Version,
            verbose_name="1",
            project=self.project,
            active=True,
            type=EXTERNAL,
        )

        result = external_rule.run(external_version)
        assert result is True
        trigger_build.assert_called_once_with(
            project=self.project,
            version=external_version,
            from_webhook=True,
        )
