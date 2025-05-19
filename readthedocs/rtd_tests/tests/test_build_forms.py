from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.forms import VersionForm
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PRIVATE, PUBLIC
from readthedocs.projects.models import HTMLFile, Project


class TestVersionForm(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=(self.user,), slug="project")

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_default_version_is_active(self):
        version = get(
            Version,
            project=self.project,
            active=False,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                "slug": version.slug,
                "active": True,
            },
            instance=version,
            project=self.project,
        )
        self.assertTrue(form.is_valid())

    def test_default_version_is_inactive(self):
        version = get(
            Version,
            project=self.project,
            active=True,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                "slug": version.slug,
                "active": False,
            },
            instance=version,
            project=self.project,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("active", form.errors)

    @override_settings(ALLOW_PRIVATE_REPOS=False)
    def test_cant_update_privacy_level(self):
        version = get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            active=True,
        )
        form = VersionForm(
            {
                "slug": version.slug,
                "active": True,
                "privacy_level": PRIVATE,
            },
            instance=version,
            project=self.project,
        )
        # The form is valid, but the field is ignored
        self.assertTrue(form.is_valid())
        self.assertEqual(version.privacy_level, PUBLIC)

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_can_update_privacy_level(self):
        version = get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            active=True,
        )
        form = VersionForm(
            {
                "slug": version.slug,
                "active": True,
                "privacy_level": PRIVATE,
            },
            instance=version,
            project=self.project,
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(version.privacy_level, PRIVATE)

    @mock.patch("readthedocs.builds.models.trigger_build", mock.MagicMock())
    @mock.patch("readthedocs.projects.tasks.search.remove_search_indexes")
    @mock.patch("readthedocs.projects.tasks.utils.remove_build_storage_paths")
    def test_resources_are_deleted_when_version_is_inactive(
        self, remove_build_storage_paths, remove_search_indexes
    ):
        version = get(
            Version,
            project=self.project,
            active=True,
        )
        another_version = get(Version, project=self.project, active=True)
        get(
            HTMLFile,
            project=self.project,
            version=version,
            name="index.html",
            path="index.html",
        )
        get(
            HTMLFile,
            project=self.project,
            version=another_version,
            name="index.html",
            path="index.html",
        )

        url = reverse(
            "project_version_detail", args=(version.project.slug, version.slug)
        )

        self.client.force_login(self.user)

        r = self.client.post(
            url,
            data={
                "slug": version.slug,
                "active": True,
                "privacy_level": PRIVATE,
            },
        )
        self.assertEqual(r.status_code, 302)
        remove_build_storage_paths.delay.assert_not_called()
        remove_search_indexes.delay.assert_not_called()
        self.assertTrue(version.imported_files.exists())
        self.assertTrue(another_version.imported_files.exists())

        r = self.client.post(
            url,
            data={
                "slug": version.slug,
                "active": False,
                "privacy_level": PRIVATE,
            },
        )
        self.assertEqual(r.status_code, 302)
        remove_build_storage_paths.delay.assert_called_once()
        remove_search_indexes.delay.assert_called_once()
        self.assertFalse(version.imported_files.exists())
        self.assertTrue(another_version.imported_files.exists())

    def test_change_slug(self):
        version = get(
            Version,
            project=self.project,
            active=True,
            slug="slug",
        )

        test_slugs = [
            "anotherslug",
            "another_slug",
            "another-slug",
        ]
        for slug in test_slugs:
            form = VersionForm(
                {
                    "slug": slug,
                    "active": True,
                    "privacy_level": PUBLIC,
                },
                instance=version,
                project=self.project,
            )
            assert form.is_valid()
            assert version.slug == slug

    def test_change_slug_wrong_value(self):
        version = get(
            Version,
            project=self.project,
            active=True,
            slug="slug",
        )

        test_slugs = (
            "???//",
            "Slug-with-uppercase",
            "no-ascíí",
            "with spaces",
            "-almost-valid",
            "no/valid",
        )
        for slug in test_slugs:
            form = VersionForm(
                {
                    "slug": slug,
                    "active": True,
                    "privacy_level": PUBLIC,
                },
                instance=version,
                project=self.project,
            )
            assert not form.is_valid()
            assert "slug" in form.errors
            assert "The slug can contain lowercase letters" in form.errors["slug"][0]

        form = VersionForm(
            {
                "slug": "",
                "active": True,
                "privacy_level": PUBLIC,
            },
            instance=version,
            project=self.project,
        )
        assert not form.is_valid()
        assert "slug" in form.errors
        assert "This field is required" in form.errors["slug"][0]

        form = VersionForm(
            {
                "slug": "a" * 256,
                "active": True,
                "privacy_level": PUBLIC,
            },
            instance=version,
            project=self.project,
        )
        assert not form.is_valid()
        assert "slug" in form.errors
        assert "Ensure this value has at most" in form.errors["slug"][0]

    def test_change_slug_already_in_use(self):
        version_one = get(
            Version,
            project=self.project,
            active=True,
            slug="one",
        )
        version_two = get(
            Version,
            project=self.project,
            active=True,
            slug="two",
        )

        form = VersionForm(
            {
                "slug": version_two.slug,
                "active": True,
                "privacy_level": PUBLIC,
            },
            instance=version_one,
            project=self.project,
        )
        assert not form.is_valid()
        assert "slug" in form.errors
        assert "A version with that slug already exists." in form.errors["slug"][0]

    def test_cant_change_slug_machine_created_versions(self):
        version = self.project.versions.get(slug="latest")
        assert version.machine

        form = VersionForm(
            {
                "slug": "change",
                "active": True,
                "privacy_level": PUBLIC,
            },
            instance=version,
            project=self.project,
        )
        assert form.is_valid()
        version.refresh_from_db()
        assert version.slug == "latest"

    @mock.patch("readthedocs.builds.models.trigger_build")
    @mock.patch("readthedocs.projects.tasks.search.remove_search_indexes")
    @mock.patch("readthedocs.projects.tasks.utils.remove_build_storage_paths")
    def test_clean_resources_when_changing_slug_of_active_version(
        self, remove_build_storage_paths, remove_search_indexes, trigger_build
    ):
        version = get(
            Version,
            project=self.project,
            active=True,
            slug="slug",
        )

        self.client.force_login(self.user)
        url = reverse(
            "project_version_detail", args=(version.project.slug, version.slug)
        )
        r = self.client.post(
            url,
            data={
                "slug": "change-me",
                "active": True,
                "privacy_level": PUBLIC,
            },
        )
        assert r.status_code == 302

        version.refresh_from_db()
        assert version.slug == "change-me"

        remove_build_storage_paths.delay.assert_called_once_with(
            [
                "html/project/slug",
                "pdf/project/slug",
                "epub/project/slug",
                "htmlzip/project/slug",
                "json/project/slug",
                "diff/project/slug",
            ]
        )
        remove_search_indexes.delay.assert_called_once_with(
            project_slug=version.project.slug,
            version_slug="slug",
        )
        trigger_build.assert_called_once_with(
            project=version.project,
            version=version,
        )

    @mock.patch("readthedocs.builds.models.trigger_build")
    @mock.patch("readthedocs.projects.tasks.search.remove_search_indexes")
    @mock.patch("readthedocs.projects.tasks.utils.remove_build_storage_paths")
    def test_dont_clean_resources_when_changing_slug_of_inactive_version(
        self, remove_build_storage_paths, remove_search_indexes, trigger_build
    ):
        version = get(
            Version,
            project=self.project,
            active=False,
            slug="slug",
        )

        self.client.force_login(self.user)
        url = reverse(
            "project_version_detail", args=(version.project.slug, version.slug)
        )
        r = self.client.post(
            url,
            data={
                "slug": "change-me",
                "active": False,
                "privacy_level": PUBLIC,
            },
        )
        assert r.status_code == 302
        version.refresh_from_db()
        assert version.slug == "change-me"

        remove_build_storage_paths.delay.assert_not_called()
        remove_search_indexes.delay.assert_not_called()
        trigger_build.assert_not_called()
