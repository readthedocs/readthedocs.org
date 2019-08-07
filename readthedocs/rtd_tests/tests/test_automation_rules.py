import mock
import pytest
from django_dynamic_fixture import get

from readthedocs.builds.constants import BRANCH, LATEST, TAG
from readthedocs.builds.models import (
    RegexAutomationRule,
    Version,
    VersionAutomationRule,
)
from readthedocs.projects.models import Project


@pytest.mark.django_db
class TestRegexAutomationRules:

    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.project = get(Project)

    @pytest.mark.parametrize(
        'version_name,regex,result',
        [
            # Matches all
            ('master', r'.*', True),
            ('latest', r'.*', True),

            # Contains match
            ('master', r'master', True),
            ('master-something', r'master', True),
            ('something-master', r'master', True),
            ('foo', r'master', False),

            # Starts with match
            ('master', r'^master', True),
            ('master-foo', r'^master', True),
            ('foo-master', r'^master', False),

            # Ends with match
            ('master', r'master$', True),
            ('foo-master', r'master$', True),
            ('master-foo', r'master$', False),

            # Exact match
            ('master', r'^master$', True),
            ('masterr', r'^master$', False),
            ('mmaster', r'^master$', False),

            # Match versions from 1.3.x series
            ('1.3.2', r'^1\.3\..*', True),
            ('1.3.3.5', r'^1\.3\..*', True),
            ('1.3.3-rc', r'^1\.3\..*', True),
            ('1.2.3', r'^1\.3\..*', False),

            # Some special regex scape characters
            ('12-a', r'^\d{2}-\D$', True),
            ('1-a', r'^\d{2}-\D$', False),

            # Groups
            ('1.3-rc', r'^(\d\.?)*-(\w*)$', True),

            # Bad regex
            ('master', r'*', False),
            ('master', r'?', False),
        ]
    )
    @pytest.mark.parametrize('version_type', [BRANCH, TAG])
    def test_match(
            self, version_name, regex, result, version_type):
        version = get(
            Version,
            verbose_name=version_name,
            project=self.project,
            active=False,
            type=version_type,
            built=False,
        )
        rule = get(
            RegexAutomationRule,
            project=self.project,
            priority=0,
            match_arg=regex,
            action=VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            version_type=version_type,
        )
        assert rule.run(version) is result

    @mock.patch('readthedocs.builds.automation_actions.trigger_build')
    def test_action_activation(self, trigger_build):
        version = get(
            Version,
            verbose_name='v2',
            project=self.project,
            active=False,
            type=TAG,
        )
        rule = get(
            RegexAutomationRule,
            project=self.project,
            priority=0,
            match_arg='.*',
            action=VersionAutomationRule.ACTIVATE_VERSION_ACTION,
            version_type=TAG,
        )
        assert rule.run(version) is True
        assert version.active is True
        trigger_build.assert_called_once()

    def test_action_set_default_version(self):
        version = get(
            Version,
            verbose_name='v2',
            project=self.project,
            active=True,
            type=TAG,
        )
        rule = get(
            RegexAutomationRule,
            project=self.project,
            priority=0,
            match_arg='.*',
            action=VersionAutomationRule.SET_DEFAULT_VERSION_ACTION,
            version_type=TAG,
        )
        assert self.project.get_default_version() == LATEST
        assert rule.run(version) is True
        assert self.project.get_default_version() == version.slug
