"""Test hosting views."""

import json
from pathlib import Path

import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.projects.constants import (
    PRIVATE,
    PUBLIC,
    SINGLE_VERSION_WITHOUT_TRANSLATIONS,
)
from readthedocs.projects.models import AddonsConfig, Domain, Project


@override_settings(
    PRODUCTION_DOMAIN="readthedocs.org",
    PUBLIC_DOMAIN="dev.readthedocs.io",
    PUBLIC_DOMAIN_USES_HTTPS=True,
    GLOBAL_ANALYTICS_CODE=None,
    RTD_ALLOW_ORGANIZATIONS=False,
)
@pytest.mark.proxito
class TestReadTheDocsConfigJson(TestCase):
    def setUp(self):
        self.user = fixture.get(User, username="testuser")
        self.user.set_password("testuser")
        self.user.save()

        self.project = fixture.get(
            Project,
            slug="project",
            name="project",
            language="en",
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
            repo="https://github.com/readthedocs/project",
            programming_language="words",
            users=[self.user],
            main_language_project=None,
            project_url="http://project.com",
        )

        for tag in ("tag", "project", "test"):
            self.project.tags.add(tag)

        self.project.versions.update(
            privacy_level=PUBLIC,
            built=True,
            active=True,
            type="tag",
            identifier="a1b2c3",
        )
        self.version = self.project.versions.get(slug=LATEST)
        self.build = fixture.get(
            Build,
            project=self.project,
            version=self.version,
            commit="a1b2c3",
            length=60,
            state="finished",
            success=True,
        )

    def _get_response_dict(self, view_name, filepath=None):
        filepath = filepath or __file__
        filename = Path(filepath).absolute().parent / "responses" / f"{view_name}.json"
        return json.load(open(filename))

    def _normalize_datetime_fields(self, obj):
        obj["projects"]["current"]["created"] = "2019-04-29T10:00:00Z"
        obj["projects"]["current"]["modified"] = "2019-04-29T12:00:00Z"
        obj["builds"]["current"]["created"] = "2019-04-29T10:00:00Z"
        obj["builds"]["current"]["finished"] = "2019-04-29T10:01:00Z"
        return obj

    def test_get_config_v0(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        assert self._normalize_datetime_fields(r.json()) == self._get_response_dict(
            "v0"
        )

    def test_get_config_v1(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        assert r.json() == self._get_response_dict("v1")

    def test_get_config_unsupported_version(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "api-version": "2.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 400
        assert r.json() == self._get_response_dict("v2")

    def test_disabled_addons_via_addons_config(self):
        addons = fixture.get(
            AddonsConfig,
            project=self.project,
        )
        addons.analytics_enabled = False
        addons.doc_diff_enabled = False
        addons.external_version_warning_enabled = False
        addons.ethicalads_enabled = False
        addons.flyout_enabled = False
        addons.hotkeys_enabled = False
        addons.search_enabled = False
        addons.stable_latest_version_warning_enabled = False
        addons.save()

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        assert r.json()["addons"]["analytics"]["enabled"] is False
        assert r.json()["addons"]["external_version_warning"]["enabled"] is False
        assert r.json()["addons"]["non_latest_version_warning"]["enabled"] is False
        assert r.json()["addons"]["doc_diff"]["enabled"] is False
        assert r.json()["addons"]["flyout"]["enabled"] is False
        assert r.json()["addons"]["search"]["enabled"] is False
        assert r.json()["addons"]["hotkeys"]["enabled"] is False

    def test_non_latest_version_warning_versions(self):
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PRIVATE,
            slug="private",
            verbose_name="private",
            built=True,
            active=True,
        )
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            slug="public-built",
            verbose_name="public-built",
            built=True,
            active=True,
        )
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            slug="public-not-built",
            verbose_name="public-not-built",
            built=False,
            active=True,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected = ["latest", "public-built"]
        assert r.json()["addons"]["non_latest_version_warning"]["versions"] == expected

    def test_flyout_versions(self):
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PRIVATE,
            slug="private",
            verbose_name="private",
            built=True,
            active=True,
        )
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            slug="public-built",
            verbose_name="public-built",
            built=True,
            active=True,
        )
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            slug="public-not-built",
            verbose_name="public-not-built",
            built=False,
            active=True,
        )
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            slug="hidden",
            verbose_name="hidden",
            built=False,
            hidden=True,
            active=True,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected = [
            {"slug": "latest", "url": "https://project.dev.readthedocs.io/en/latest/"},
            {
                "slug": "public-built",
                "url": "https://project.dev.readthedocs.io/en/public-built/",
            },
        ]
        assert r.json()["addons"]["flyout"]["versions"] == expected

    def test_flyout_translations(self):
        fixture.get(
            Project,
            slug="translation",
            main_language_project=self.project,
            language="ja",
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected = [
            {"slug": "en", "url": "https://project.dev.readthedocs.io/en/latest/"},
            {"slug": "ja", "url": "https://project.dev.readthedocs.io/ja/latest/"},
        ]
        assert r.json()["addons"]["flyout"]["translations"] == expected

    def test_flyout_downloads(self):
        fixture.get(
            Version,
            project=self.project,
            privacy_level=PUBLIC,
            slug="offline",
            verbose_name="offline",
            built=True,
            has_pdf=True,
            has_epub=True,
            has_htmlzip=True,
            active=True,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/offline/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected = [
            {
                "name": "PDF",
                "url": "//project.dev.readthedocs.io/_/downloads/en/offline/pdf/",
            },
            {
                "name": "HTML",
                "url": "//project.dev.readthedocs.io/_/downloads/en/offline/htmlzip/",
            },
            {
                "name": "Epub",
                "url": "//project.dev.readthedocs.io/_/downloads/en/offline/epub/",
            },
        ]
        assert r.json()["addons"]["flyout"]["downloads"] == expected

    def test_flyout_single_version_project(self):
        self.version.has_pdf = True
        self.version.has_epub = True
        self.version.has_htmlzip = True
        self.version.save()

        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected = []
        assert r.json()["addons"]["flyout"]["versions"] == expected

        expected = [
            {
                "name": "PDF",
                "url": "//project.dev.readthedocs.io/_/downloads/en/latest/pdf/",
            },
            {
                "name": "HTML",
                "url": "//project.dev.readthedocs.io/_/downloads/en/latest/htmlzip/",
            },
            {
                "name": "Epub",
                "url": "//project.dev.readthedocs.io/_/downloads/en/latest/epub/",
            },
        ]
        assert r.json()["addons"]["flyout"]["downloads"] == expected

    def test_builds_current_is_latest_one(self):
        # Create 10 successful build objects
        # The latest one (ordered by date) will be ``a1b2c3-9``
        for i in range(10):
            fixture.get(
                Build,
                date=timezone.now(),
                project=self.project,
                version=self.version,
                commit=f"a1b2c3-{i}",
                length=60,
                state="finished",
                success=True,
            )

        # Latest failed build
        fixture.get(
            Build,
            date=timezone.now(),
            project=self.project,
            version=self.version,
            commit=f"a1b2c3-failed",
            length=60,
            state="finished",
            success=False,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        # ``a1b2c3-9``is the latest successful build object created
        assert r.json()["builds"]["current"]["commit"] == "a1b2c3-9"

    def test_builds_current_is_latest_one_without_url_parameter(self):
        # Create 10 successful build objects
        # The latest one (ordered by date) will be ``a1b2c3-9``
        for i in range(10):
            fixture.get(
                Build,
                date=timezone.now(),
                project=self.project,
                version=self.version,
                commit=f"a1b2c3-{i}",
                length=60,
                state="finished",
                success=True,
            )

        # Latest failed build
        fixture.get(
            Build,
            date=timezone.now(),
            project=self.project,
            version=self.version,
            commit=f"a1b2c3-failed",
            length=60,
            state="finished",
            success=False,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "project-slug": "project",
                "version-slug": "latest",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        # ``a1b2c3-9``is the latest successful build object created
        assert r.json()["builds"]["current"]["commit"] == "a1b2c3-9"

    def test_project_subproject(self):
        subproject = fixture.get(
            Project,
            slug="subproject",
            repo="https://github.com/readthedocs/subproject",
            privacy_level=PUBLIC,
        )
        subproject.versions.update(privacy_level=PUBLIC, built=True, active=True)
        self.project.add_subproject(subproject)

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/projects/subproject/en/latest/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        assert r.json()["projects"]["current"]["id"] == subproject.pk
        assert r.json()["projects"]["current"]["slug"] == subproject.slug
        assert (
            r.json()["projects"]["current"]["repository"]["url"]
            == "https://github.com/readthedocs/subproject"
        )

    def test_flyout_subproject_urls(self):
        translation = fixture.get(
            Project,
            slug="translation",
            language="es",
            repo="https://github.com/readthedocs/subproject",
        )
        translation.versions.update(
            built=True,
            active=True,
        )
        subproject = fixture.get(
            Project, slug="subproject", repo="https://github.com/readthedocs/subproject"
        )
        self.project.add_subproject(subproject)
        subproject.translations.add(translation)
        subproject.save()

        fixture.get(Version, slug="v1", project=subproject)
        fixture.get(Version, slug="v2.3", project=subproject)
        subproject.versions.update(
            privacy_level=PUBLIC,
            built=True,
            active=True,
            hidden=False,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/projects/subproject/en/latest/",
                "client-version": "0.6.0",
                "api-version": "0.1.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected_versions = [
            {
                "slug": "latest",
                "url": "https://project.dev.readthedocs.io/projects/subproject/en/latest/",
            },
            {
                "slug": "v1",
                "url": "https://project.dev.readthedocs.io/projects/subproject/en/v1/",
            },
            {
                "slug": "v2.3",
                "url": "https://project.dev.readthedocs.io/projects/subproject/en/v2.3/",
            },
        ]
        assert r.json()["addons"]["flyout"]["versions"] == expected_versions

        expected_translations = [
            {
                "slug": "en",
                "url": "https://project.dev.readthedocs.io/projects/subproject/en/latest/",
            },
            {
                "slug": "es",
                "url": "https://project.dev.readthedocs.io/projects/subproject/es/latest/",
            },
        ]
        assert r.json()["addons"]["flyout"]["translations"] == expected_translations

    def test_send_project_not_version_slugs(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "0.1.0",
                "client-version": "0.6.0",
                "project-slug": self.project.slug,
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 400
        assert r.json() == {
            "error": "'project-slug' and 'version-slug' GET attributes are required when not sending 'url'"
        }

    def test_send_version_not_project_slugs(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "0.1.0",
                "client-version": "0.6.0",
                "version-slug": self.version.slug,
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 400
        assert r.json() == {
            "error": "'project-slug' and 'version-slug' GET attributes are required when not sending 'url'"
        }

    def test_send_project_version_slugs(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "0.1.0",
                "client-version": "0.6.0",
                "project-slug": self.project.slug,
                "version-slug": self.version.slug,
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        expected_response = self._get_response_dict("v0")
        # Remove `addons.doc_diff` from the response because it's not present when `url=` is not sent
        expected_response["addons"].pop("doc_diff")

        assert self._normalize_datetime_fields(r.json()) == expected_response

    def test_send_project_version_slugs_and_url(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "0.1.0",
                "client-version": "0.6.0",
                "url": "https://project.dev.readthedocs.io/en/latest/",
                # When sending `url=`, slugs are ignored
                "project-slug": "different-project-slug-than-url",
                "version-slug": "different-version-slug-than-url",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        assert self._normalize_datetime_fields(r.json()) == self._get_response_dict(
            "v0"
        )

    def test_custom_domain_url(self):
        fixture.get(
            Domain,
            domain="docs.example.com",
            canonical=True,
            project=self.project,
        )
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "0.1.0",
                "client-version": "0.6.0",
                "url": "https://docs.example.com/en/latest/",
            },
            secure=True,
            headers={
                "host": "docs.example.com",
            },
        )
        assert r.status_code == 200
        expected_versions = [
            {
                "url": "https://docs.example.com/en/latest/",
                "slug": "latest",
            },
        ]
        assert r.json()["addons"]["flyout"]["versions"] == expected_versions

    def test_number_of_queries_project_version_slug(self):
        # The number of queries should not increase too much, even if we change
        # some of the responses from the API. This test will help us to
        # understand how much this number varies depending on the changes we do.

        # Create many versions for this project.
        # These versions will call `resolver.resolve` to generate the URL returned for the flyout.
        # No matter how big the number of versions is, the amount of queries should stay the same.
        for i in range(35):
            name = f"public-built-{i}"
            fixture.get(
                Version,
                project=self.project,
                privacy_level=PUBLIC,
                slug=name,
                verbose_name=name,
                built=True,
                active=True,
            )

        with self.assertNumQueries(21):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "api-version": "0.1.0",
                    "client-version": "0.6.0",
                    "project-slug": "project",
                    "version-slug": "latest",
                },
                secure=True,
                headers={
                    "host": "project.dev.readthedocs.io",
                },
            )
        assert r.status_code == 200

    def test_number_of_queries_url(self):
        for i in range(35):
            name = f"public-built-{i}"
            fixture.get(
                Version,
                project=self.project,
                privacy_level=PUBLIC,
                slug=name,
                verbose_name=name,
                built=True,
                active=True,
            )

        with self.assertNumQueries(21):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project.dev.readthedocs.io/en/latest/",
                    "api-version": "0.1.0",
                },
                secure=True,
                headers={
                    "host": "project.dev.readthedocs.io",
                },
            )
        assert r.status_code == 200

    def test_number_of_queries_url_subproject(self):
        subproject = fixture.get(
            Project,
            slug="subproject",
            repo="https://github.com/readthedocs/subproject",
            privacy_level=PUBLIC,
        )
        subproject.versions.update(privacy_level=PUBLIC, built=True, active=True)
        self.project.add_subproject(subproject)

        for i in range(35):
            name = f"public-built-{i}"
            fixture.get(
                Version,
                project=subproject,
                privacy_level=PUBLIC,
                slug=name,
                verbose_name=name,
                built=True,
                active=True,
            )

        with self.assertNumQueries(25):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project.dev.readthedocs.io/projects/subproject/en/latest/",
                    "client-version": "0.6.0",
                    "api-version": "0.1.0",
                },
                secure=True,
                headers={
                    "host": "project.dev.readthedocs.io",
                },
            )
        assert r.status_code == 200

    def test_number_of_queries_url_translations(self):
        # Create multiple translations to be shown in the flyout
        for language in ["ja", "es", "ru", "pt-br"]:
            slug = f"translation-{language}"
            fixture.get(
                Project,
                slug=slug,
                main_language_project=self.project,
                language=language,
            )

        with self.assertNumQueries(25):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project.dev.readthedocs.io/en/latest/",
                    "client-version": "0.6.0",
                    "api-version": "0.1.0",
                },
                secure=True,
                headers={
                    "host": "project.dev.readthedocs.io",
                },
            )
        assert r.status_code == 200
