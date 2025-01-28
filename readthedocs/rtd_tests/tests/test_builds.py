import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import (
    BRANCH,
    EXTERNAL,
    GENERIC_EXTERNAL_VERSION_NAME,
    GITHUB_EXTERNAL_VERSION_NAME,
    GITLAB_EXTERNAL_VERSION_NAME,
)
from readthedocs.builds.models import Build, Version
from readthedocs.projects.models import Project


class BuildModelTests(TestCase):
    fixtures = ["test_data", "eric"]

    def setUp(self):
        self.eric = User.objects.get(username="eric")
        self.eric.set_password("test")
        self.eric.save()

        self.project = get(Project)
        self.project.users.add(self.eric)
        self.version = get(
            Version,
            project=self.project,
            type=BRANCH,
            slug="v2",
            identifier="a1b2c3",
            verbose_name="v2",
        )

        self.pip = Project.objects.get(slug="pip")
        self.external_version = get(
            Version,
            identifier="9F86D081884C7D659A2FEAA0C55AD015A",
            verbose_name="9999",
            slug="pr-9999",
            project=self.pip,
            active=True,
            type=EXTERNAL,
        )
        self.pip_version = get(
            Version,
            identifier="origin/stable",
            verbose_name="stable",
            slug="stable",
            project=self.pip,
            active=True,
            type=BRANCH,
        )

    def test_get_previous_build(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )
        build_two = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 2},
        )
        build_three = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 3},
            success=False,
        )

        self.assertIsNone(build_one.previous)
        self.assertEqual(build_two.previous, build_one)
        self.assertEqual(build_three.previous, build_two)
        self.assertEqual(build_three.previous.previous, build_one)

    def test_normal_save_config(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build.config = {"version": 1}
        build.save()
        self.assertEqual(build.config, {"version": 1})

        build.config = {"version": 2}
        build.save()
        self.assertEqual(build.config, {"version": 2})

    def test_save_same_config(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {"version": 2}
        build_two.save()

        self.assertEqual(build_two.config, {"version": 2})

    def test_save_same_config_previous_empty(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {}
        build_two.save()

        self.assertEqual(build_two.config, {})
        build_two.config = {"version": 2}
        build_two.save()
        self.assertEqual(build_two.config, {"version": 2})

    def test_do_not_save_same_config(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {"version": 1}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {"version": 1}
        build_two.save()
        self.assertEqual(build_two._config, {Build.CONFIG_KEY: build_one.pk})
        self.assertEqual(build_two.config, {"version": 1})

    def test_do_not_save_same_config_nested(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {"version": 1}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {"version": 1}
        build_two.save()

        build_three = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_three.config = {"version": 1}
        build_three.save()

        build_four = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_four.config = {"version": 2}
        build_four.save()

        self.assertEqual(build_one.config, {"version": 1})
        self.assertEqual(build_one._config, {"version": 1})

        self.assertEqual(build_two._config, {Build.CONFIG_KEY: build_one.pk})
        self.assertEqual(build_three._config, {Build.CONFIG_KEY: build_one.pk})

        self.assertEqual(build_two.config, {"version": 1})
        self.assertEqual(build_three.config, {"version": 1})

        self.assertEqual(build_four.config, {"version": 2})
        self.assertEqual(build_four._config, {"version": 2})

    def test_do_not_reference_empty_configs(self):
        build_one = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_one.config = {}
        build_one.save()

        build_two = get(
            Build,
            project=self.project,
            version=self.version,
        )
        build_two.config = {}
        build_two.save()
        self.assertEqual(build_two._config, {})
        self.assertEqual(build_two.config, {})

    def test_build_is_stale(self):
        now = timezone.now()

        build_one = get(
            Build,
            project=self.project,
            version=self.version,
            date=now - datetime.timedelta(minutes=8),
            state="finished",
        )
        build_two = get(
            Build,
            project=self.project,
            version=self.version,
            date=now - datetime.timedelta(minutes=6),
            state="triggered",
        )
        build_three = get(
            Build,
            project=self.project,
            version=self.version,
            date=now - datetime.timedelta(minutes=2),
            state="triggered",
        )

        self.assertFalse(build_one.is_stale)
        self.assertTrue(build_two.is_stale)
        self.assertFalse(build_three.is_stale)

    def test_build_is_external(self):
        # Turn the build version to EXTERNAL type.
        self.version.type = EXTERNAL
        self.version.save()

        external_build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertTrue(external_build.is_external)

    def test_build_is_not_external(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertFalse(build.is_external)

    def test_no_external_version_name(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertEqual(build.external_version_name, None)

    def test_external_version_name_github(self):
        self.project.repo = "https://github.com/test/test/"
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)

        self.assertEqual(
            external_build.external_version_name, GITHUB_EXTERNAL_VERSION_NAME
        )

    def test_external_version_name_gitlab(self):
        self.project.repo = "https://gitlab.com/test/test/"
        self.project.save()

        external_version = get(Version, project=self.project, type=EXTERNAL)
        external_build = get(Build, project=self.project, version=external_version)

        self.assertEqual(
            external_build.external_version_name, GITLAB_EXTERNAL_VERSION_NAME
        )

    def test_external_version_name_generic(self):
        # Turn the build version to EXTERNAL type.
        self.version.type = EXTERNAL
        self.version.save()

        external_build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertEqual(
            external_build.external_version_name, GENERIC_EXTERNAL_VERSION_NAME
        )

    def test_get_commit_url_external_version_github(self):
        self.pip.repo = "https://github.com/pypa/pip"
        self.pip.save()

        external_build = get(
            Build,
            project=self.pip,
            version=self.external_version,
            _config={"version": 1},
        )
        expected_url = "https://github.com/pypa/pip/pull/{number}/commits/{sha}".format(
            number=self.external_version.verbose_name, sha=external_build.commit
        )
        self.assertEqual(external_build.get_commit_url(), expected_url)

    def test_get_commit_url_external_version_gitlab(self):
        self.pip.repo = "https://gitlab.com/pypa/pip"
        self.pip.save()

        external_build = get(
            Build,
            project=self.pip,
            version=self.external_version,
            _config={"version": 1},
        )
        expected_url = (
            "https://gitlab.com/pypa/pip/commit/" "{commit}?merge_request_iid={number}"
        ).format(
            number=self.external_version.verbose_name, commit=external_build.commit
        )
        self.assertEqual(external_build.get_commit_url(), expected_url)

    def test_get_commit_url_internal_version(self):
        build = get(
            Build,
            project=self.pip,
            version=self.pip_version,
            _config={"version": 1},
        )
        expected_url = "https://github.com/pypa/pip/commit/{sha}".format(
            sha=build.commit
        )
        self.assertEqual(build.get_commit_url(), expected_url)

    def test_version_deleted(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            commit=self.version.identifier,
        )

        self.assertEqual(Build.objects.all().count(), 1)
        self.assertEqual(build.version_name, "v2")
        self.assertEqual(build.version_slug, "v2")
        self.assertEqual(build.version_type, BRANCH)
        self.assertEqual(build.commit, "a1b2c3")

        self.version.delete()
        build.refresh_from_db()

        self.assertEqual(Build.objects.all().count(), 1)
        self.assertIsNone(build.version)
        self.assertEqual(build.version_name, "v2")
        self.assertEqual(build.version_slug, "v2")
        self.assertEqual(build.version_type, BRANCH)
        self.assertEqual(build.commit, "a1b2c3")

    def test_can_rebuild_with_regular_version(self):
        build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertFalse(build.can_rebuild)

    def test_can_rebuild_with_external_active_version(self):
        # Turn the build version to EXTERNAL type.
        self.version.type = EXTERNAL
        self.version.active = True
        self.version.save()

        external_build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertTrue(external_build.can_rebuild)

    def test_can_rebuild_with_external_inactive_version(self):
        # Turn the build version to EXTERNAL type.
        self.version.type = EXTERNAL
        self.version.active = False
        self.version.save()

        external_build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertFalse(external_build.can_rebuild)

    def test_can_rebuild_with_old_build(self):
        # Turn the build version to EXTERNAL type.
        self.version.type = EXTERNAL
        self.version.active = True
        self.version.save()

        old_external_build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        latest_external_build = get(
            Build,
            project=self.project,
            version=self.version,
            _config={"version": 1},
        )

        self.assertFalse(old_external_build.can_rebuild)
        self.assertTrue(latest_external_build.can_rebuild)
