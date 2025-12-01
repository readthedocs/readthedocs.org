"""Test hosting views."""

import json
from pathlib import Path
from unittest import mock

import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED, EXTERNAL, LATEST
from readthedocs.builds.models import Build, Version
from readthedocs.filetreediff.dataclasses import (
    FileTreeDiff,
    FileTreeDiffManifestFile,
    FileTreeDiffFileStatus,
    FileTreeDiffManifest,
)
from readthedocs.projects.constants import (
    ADDONS_FLYOUT_SORTING_ALPHABETICALLY,
    ADDONS_FLYOUT_SORTING_CALVER,
    ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING,
    MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
    PRIVATE,
    PUBLIC,
    SINGLE_VERSION_WITHOUT_TRANSLATIONS,
)
from readthedocs.projects.models import Domain, Project


@override_settings(
    PRODUCTION_DOMAIN="readthedocs.org",
    PUBLIC_DOMAIN="dev.readthedocs.io",
    PUBLIC_DOMAIN_USES_HTTPS=True,
    GLOBAL_ANALYTICS_CODE=None,
    RTD_ALLOW_ORGANIZATIONS=False,
    RTD_EXTERNAL_VERSION_DOMAIN="dev.readthedocs.build",
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
            versioning_scheme=MULTIPLE_VERSIONS_WITH_TRANSLATIONS,
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
        self.version.identifier = "master"
        self.version.save()
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
        try:
            obj["projects"]["current"]["created"] = "2019-04-29T10:00:00Z"
            obj["projects"]["current"]["modified"] = "2019-04-29T12:00:00Z"
        except:
            pass

        try:
            obj["builds"]["current"]["created"] = "2019-04-29T10:00:00Z"
            obj["builds"]["current"]["finished"] = "2019-04-29T10:01:00Z"
        except:
            pass
        return obj

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
        assert self._normalize_datetime_fields(r.json()) == self._get_response_dict(
            "v1"
        )

    def test_get_config_v2(self):
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
        assert r.status_code == 200
        assert r.json() == self._get_response_dict("v2")

    def test_get_config_unsupported_version(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "api-version": "3.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 400
        assert r.json() == self._get_response_dict("v3")

    def test_disabled_addons_via_addons_config(self):
        self.project.addons.analytics_enabled = False
        self.project.addons.doc_diff_enabled = False
        self.project.addons.external_version_warning_enabled = False
        self.project.addons.ethicalads_enabled = False
        self.project.addons.flyout_enabled = False
        self.project.addons.hotkeys_enabled = False
        self.project.addons.search_enabled = False
        self.project.addons.notifications_enabled = False
        self.project.addons.notifications_show_on_latest = False
        self.project.addons.notifications_show_on_non_stable = False
        self.project.addons.notifications_show_on_external = False
        self.project.addons.save()

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        assert r.json()["addons"]["analytics"]["enabled"] is False
        assert r.json()["addons"]["notifications"]["enabled"] is False
        assert r.json()["addons"]["notifications"]["show_on_latest"] is False
        assert r.json()["addons"]["notifications"]["show_on_non_stable"] is False
        assert r.json()["addons"]["notifications"]["show_on_external"] is False
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
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected = ["latest", "public-built"]
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

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
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        assert len(r.json()["versions"]["active"]) == 2
        assert r.json()["versions"]["active"][0]["slug"] == "latest"
        assert (
            r.json()["versions"]["active"][0]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/en/latest/"
        )
        assert r.json()["versions"]["active"][1]["slug"] == "public-built"
        assert (
            r.json()["versions"]["active"][1]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/en/public-built/"
        )

    def test_flyout_translations(self):
        translation_ja = fixture.get(
            Project,
            slug="translation",
            main_language_project=self.project,
            language="ja",
            privacy_level=PUBLIC,
        )
        translation_ja.versions.update(
            built=True,
            active=True,
            privacy_level=PUBLIC,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        # Hitting the English version of the docs, will return Japanese as translation
        assert len(r.json()["projects"]["translations"]) == 1
        assert r.json()["projects"]["translations"][0]["slug"] == "translation"
        assert r.json()["projects"]["translations"][0]["language"]["code"] == "ja"
        assert (
            r.json()["projects"]["translations"][0]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/ja/latest/"
        )

        # Hitting the Japanese version of the docs, will return English as translation
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/ja/latest/",
                "client-version": "0.6.0",
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        assert len(r.json()["projects"]["translations"]) == 1
        assert r.json()["projects"]["translations"][0]["slug"] == "project"
        assert r.json()["projects"]["translations"][0]["language"]["code"] == "en"
        assert (
            r.json()["projects"]["translations"][0]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/en/latest/"
        )

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
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected = {
            "pdf": "https://project.dev.readthedocs.io/_/downloads/en/offline/pdf/",
            "htmlzip": "https://project.dev.readthedocs.io/_/downloads/en/offline/htmlzip/",
            "epub": "https://project.dev.readthedocs.io/_/downloads/en/offline/epub/",
        }
        assert r.json()["versions"]["current"]["downloads"] == expected

    def test_number_of_queries_versions_with_downloads(self):
        for i in range(10):
            fixture.get(
                Version,
                project=self.project,
                privacy_level=PUBLIC,
                slug=f"offline-{i}",
                verbose_name=f"offline-{i}",
                built=True,
                has_pdf=True,
                has_epub=True,
                has_htmlzip=True,
                active=True,
            )

        with self.assertNumQueries(13):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project.dev.readthedocs.io/en/offline/",
                    "client-version": "0.6.0",
                    "api-version": "1.0.0",
                },
                secure=True,
                headers={
                    "host": "project.dev.readthedocs.io",
                },
            )
            assert r.status_code == 200

    def test_flyout_single_version_project(self):
        self.version.has_pdf = True
        self.version.has_epub = True
        self.version.has_htmlzip = True
        self.version.save()

        # Add extra built and active versions to emulate a project that went
        # from multiple versions to single version.
        # These versions shouldn't be included in the `versions.active` field.
        for i in range(5):
            fixture.get(
                Version,
                privacy_level=PUBLIC,
                active=True,
                built=True,
                project=self.project,
            )

        self.project.versioning_scheme = SINGLE_VERSION_WITHOUT_TRANSLATIONS
        self.project.save()

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/",
                "client-version": "0.6.0",
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200
        expected = ["latest"]
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        expected = {
            "pdf": "https://project.dev.readthedocs.io/_/downloads/en/latest/pdf/",
            "htmlzip": "https://project.dev.readthedocs.io/_/downloads/en/latest/htmlzip/",
            "epub": "https://project.dev.readthedocs.io/_/downloads/en/latest/epub/",
        }
        assert r.json()["versions"]["current"]["downloads"] == expected

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
                "api-version": "1.0.0",
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
                "api-version": "1.0.0",
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
                "api-version": "1.0.0",
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
            privacy_level=PUBLIC,
        )
        translation.versions.update(
            built=True,
            active=True,
        )
        subproject = fixture.get(
            Project,
            slug="subproject",
            repo="https://github.com/readthedocs/subproject",
            privacy_level=PUBLIC,
        )
        self.project.add_subproject(subproject)
        subproject.translations.add(translation)
        subproject.save()

        fixture.get(Version, slug="v1", project=subproject, privacy_level=PUBLIC)
        fixture.get(Version, slug="v2.3", project=subproject, privacy_level=PUBLIC)
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
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        assert len(r.json()["versions"]["active"]) == 3
        assert r.json()["versions"]["active"][0]["slug"] == "latest"
        assert (
            r.json()["versions"]["active"][0]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/projects/subproject/en/latest/"
        )
        assert r.json()["versions"]["active"][1]["slug"] == "v2.3"
        assert (
            r.json()["versions"]["active"][1]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/projects/subproject/en/v2.3/"
        )
        assert r.json()["versions"]["active"][2]["slug"] == "v1"
        assert (
            r.json()["versions"]["active"][2]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/projects/subproject/en/v1/"
        )

        assert len(r.json()["projects"]["translations"]) == 1
        assert r.json()["projects"]["translations"][0]["slug"] == "translation"
        assert r.json()["projects"]["translations"][0]["language"]["code"] == "es"
        assert (
            r.json()["projects"]["translations"][0]["urls"]["documentation"]
            == "https://project.dev.readthedocs.io/projects/subproject/es/latest/"
        )

    def test_send_project_not_version_slugs(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "1.0.0",
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
                "api-version": "1.0.0",
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
                "api-version": "1.0.0",
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
        expected_response = self._get_response_dict("v1")
        # Remove `addons.doc_diff` from the response because it's not present when `url=` is not sent
        expected_response["addons"].pop("doc_diff")
        expected_response["readthedocs"]["resolver"]["filename"] = None

        assert self._normalize_datetime_fields(r.json()) == expected_response

    def test_send_project_version_slugs_and_url(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "1.0.0",
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
            "v1"
        )

    def test_send_project_slug_and_notfound_version_slug(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "1.0.0",
                "client-version": "0.6.0",
                "project-slug": self.project.slug,
                "version-slug": "not-found",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 200

        expected_response = self._get_response_dict("v1")

        # Since there is no version, there are some fields that we need to change from the default response
        del expected_response["addons"]["doc_diff"]
        expected_response["builds"]["current"] = None
        expected_response["versions"]["current"] = None
        expected_response["readthedocs"]["resolver"]["filename"] = None
        expected_response["addons"]["search"]["default_filter"] = f"project:{self.project.slug}"
        assert self._normalize_datetime_fields(r.json()) == expected_response


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
                "api-version": "1.0.0",
                "client-version": "0.6.0",
                "url": "https://docs.example.com/en/latest/",
            },
            secure=True,
            headers={
                "host": "docs.example.com",
            },
        )
        assert r.status_code == 200
        assert len(r.json()["versions"]["active"]) == 1
        assert r.json()["versions"]["active"][0]["slug"] == "latest"
        assert (
            r.json()["versions"]["active"][0]["urls"]["documentation"]
            == "https://docs.example.com/en/latest/"
        )

    def test_linkpreviews(self):
        self.project.addons.linkpreviews_enabled = True
        self.project.addons.save()

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "1.0.0",
                "client-version": "0.6.0",
                "url": "https://project.dev.readthedocs.io/en/latest/",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        expected = {
            "enabled": True,
            "selector": None,
        }

        assert r.status_code == 200
        assert r.json()["addons"]["linkpreviews"] == expected

    def test_non_existent_project(self):
        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "api-version": "1.0.0",
                "client-version": "0.6.0",
                "project-slug": "non-existent-project",
                "version-slug": "latest",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )
        assert r.status_code == 404
        assert r.json() == {"detail": "No Project matches the given query."}

    def test_number_of_queries_project_version_slug(self):
        # The number of queries should not increase too much, even if we change
        # some of the responses from the API. This test will help us to
        # understand how much this number varies depending on the changes we do.

        # Create many versions for this project.
        # These versions will call `resolver.resolve` to generate the URL returned for
        # `projects.translations` and `versions.active` fields.
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

        with self.assertNumQueries(16):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "api-version": "1.0.0",
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

        with self.assertNumQueries(17):
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

        with self.assertNumQueries(18):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project.dev.readthedocs.io/projects/subproject/en/latest/",
                    "client-version": "0.6.0",
                    "api-version": "1.0.0",
                },
                secure=True,
                headers={
                    "host": "project.dev.readthedocs.io",
                },
            )
        assert r.status_code == 200

        # Test parent project has fewer queries
        with self.assertNumQueries(16):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project.dev.readthedocs.io/en/latest/",
                    "client-version": "0.6.0",
                    "api-version": "1.0.0",
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

        with self.assertNumQueries(26):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project.dev.readthedocs.io/en/latest/",
                    "client-version": "0.6.0",
                    "api-version": "1.0.0",
                },
                secure=True,
                headers={
                    "host": "project.dev.readthedocs.io",
                },
            )
        assert r.status_code == 200

    @override_settings(
        RTD_FILETREEDIFF_ALL=True,
    )
    @mock.patch("readthedocs.proxito.views.hosting.get_diff")
    def test_file_tree_diff_ignored_files(self, get_diff):
        ignored_files = [
            "ignored.html",
            "archives/*",
        ]

        self.project.addons.filetreediff_enabled = True
        self.project.addons.filetreediff_ignored_files = ignored_files
        self.project.addons.save()

        get_diff.return_value = FileTreeDiff(
            current_version=self.version,
            current_version_build=self.build,
            base_version=self.version,
            base_version_build=self.build,
            files=[
                ("tags/newtag.html", FileTreeDiffFileStatus.added),
                ("ignored.html", FileTreeDiffFileStatus.modified),
                ("archives/2025.html", FileTreeDiffFileStatus.modified),
                ("changelog/2025.2.html", FileTreeDiffFileStatus.modified),
                ("deleted.html", FileTreeDiffFileStatus.deleted),
            ],
            outdated=False,
        )

        r = self.client.get(
            reverse("proxito_readthedocs_docs_addons"),
            {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "1.0.0",
            },
            secure=True,
            headers={
                "host": "project.dev.readthedocs.io",
            },
        )

        expected = {
            "enabled": True,
            "outdated": False,
            "diff": {
                "added": [
                    {
                        "filename": "tags/newtag.html",
                        "urls": {
                            "current": "https://project.dev.readthedocs.io/en/latest/tags/newtag.html",
                            "base": "https://project.dev.readthedocs.io/en/latest/tags/newtag.html",
                        },
                    },
                ],
                "deleted": [
                    {
                        "filename": "deleted.html",
                        "urls": {
                            "current": "https://project.dev.readthedocs.io/en/latest/deleted.html",
                            "base": "https://project.dev.readthedocs.io/en/latest/deleted.html",
                        },
                    },
                ],
                "modified": [
                    {
                        "filename": "changelog/2025.2.html",
                        "urls": {
                            "current": "https://project.dev.readthedocs.io/en/latest/changelog/2025.2.html",
                            "base": "https://project.dev.readthedocs.io/en/latest/changelog/2025.2.html",
                        },
                    },
                ],
            },
        }
        assert r.status_code == 200
        assert r.json()["addons"]["filetreediff"] == expected

    @mock.patch("readthedocs.filetreediff.get_manifest")
    def test_file_tree_diff(self, get_manifest):
        self.project.addons.filetreediff_enabled = True
        self.project.addons.save()
        pr_version = get(
            Version,
            project=self.project,
            slug="123",
            active=True,
            built=True,
            privacy_level=PUBLIC,
            type=EXTERNAL,
        )
        pr_build = get(
            Build,
            project=self.project,
            version=pr_version,
            commit="a1b2c3",
            state=BUILD_STATE_FINISHED,
            success=True,
        )
        get_manifest.side_effect = [
            FileTreeDiffManifest(
                build_id=pr_build.id,
                files=[
                    FileTreeDiffManifestFile(
                        path="index.html",
                        main_content_hash="hash1",
                    ),
                    FileTreeDiffManifestFile(
                        path="tutorial/index.html",
                        main_content_hash="hash1",
                    ),
                    FileTreeDiffManifestFile(
                        path="new-file.html",
                        main_content_hash="hash1",
                    ),
                ],
            ),
            FileTreeDiffManifest(
                build_id=self.build.id,
                files=[
                    FileTreeDiffManifestFile(
                        path="index.html",
                        main_content_hash="hash1",
                    ),
                    FileTreeDiffManifestFile(
                        path="tutorial/index.html",
                        main_content_hash="hash-changed",
                    ),
                    FileTreeDiffManifestFile(
                        path="deleted.html",
                        main_content_hash="hash-deleted",
                    ),
                ],
            ),
        ]
        with self.assertNumQueries(20):
            r = self.client.get(
                reverse("proxito_readthedocs_docs_addons"),
                {
                    "url": "https://project--123.dev.readthedocs.build/en/123/",
                    "client-version": "0.6.0",
                    "api-version": "1.0.0",
                },
                secure=True,
                headers={
                    "host": "project--123.dev.readthedocs.build",
                },
            )
        assert r.status_code == 200
        filetreediff_response = r.json()["addons"]["filetreediff"]
        assert filetreediff_response == {
            "enabled": True,
            "outdated": False,
            "diff": {
                "added": [
                    {
                        "filename": "new-file.html",
                        "urls": {
                            "current": "https://project--123.dev.readthedocs.build/en/123/new-file.html",
                            "base": "https://project.dev.readthedocs.io/en/latest/new-file.html",
                        },
                    },
                ],
                "deleted": [
                    {
                        "filename": "deleted.html",
                        "urls": {
                            "current": "https://project--123.dev.readthedocs.build/en/123/deleted.html",
                            "base": "https://project.dev.readthedocs.io/en/latest/deleted.html",
                        },
                    },
                ],
                "modified": [
                    {
                        "filename": "tutorial/index.html",
                        "urls": {
                            "current": "https://project--123.dev.readthedocs.build/en/123/tutorial/index.html",
                            "base": "https://project.dev.readthedocs.io/en/latest/tutorial/index.html",
                        },
                    },
                ],
            },
        }

    def test_version_ordering(self):
        for slug in ["1.0", "1.2", "1.12", "2.0", "2020.01.05", "a-slug", "z-slug"]:
            fixture.get(
                Version,
                project=self.project,
                privacy_level=PUBLIC,
                slug=slug,
                verbose_name=slug,
                built=True,
                active=True,
            )
        self.project.update_stable_version()
        self.project.versions.update(
            privacy_level=PUBLIC,
            built=True,
            active=True,
        )

        kwargs = {
            "path": reverse("proxito_readthedocs_docs_addons"),
            "data": {
                "url": "https://project.dev.readthedocs.io/en/latest/",
                "client-version": "0.6.0",
                "api-version": "1.0.0",
            },
            "secure": True,
            "headers": {
                "host": "project.dev.readthedocs.io",
            },
        }

        # Default ordering (SemVer)
        expected = [
            "latest",
            "stable",
            "2020.01.05",
            "2.0",
            "1.12",
            "1.2",
            "1.0",
            "z-slug",
            "a-slug",
        ]
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        self.project.refresh_from_db()
        addons = self.project.addons

        # The order of latest and stable doesn't change when using semver.
        addons.flyout_sorting_latest_stable_at_beginning = False
        addons.save()
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        addons.flyout_sorting = ADDONS_FLYOUT_SORTING_ALPHABETICALLY
        addons.flyout_sorting_latest_stable_at_beginning = True
        addons.save()
        expected = [
            "z-slug",
            "stable",
            "latest",
            "a-slug",
            "2020.01.05",
            "2.0",
            "1.2",
            "1.12",
            "1.0",
        ]
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        # The order of latest and stable doesn't change when using alphabetical sorting.
        addons.flyout_sorting_latest_stable_at_beginning = False
        addons.save()
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        addons.flyout_sorting = ADDONS_FLYOUT_SORTING_PYTHON_PACKAGING
        addons.flyout_sorting_latest_stable_at_beginning = True
        addons.save()
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        expected = [
            "latest",
            "stable",
            "2020.01.05",
            "2.0",
            "1.12",
            "1.2",
            "1.0",
            "z-slug",
            "a-slug",
        ]
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        addons.flyout_sorting_latest_stable_at_beginning = False
        addons.save()
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        expected = [
            "2020.01.05",
            "2.0",
            "1.12",
            "1.2",
            "1.0",
            "z-slug",
            "stable",
            "latest",
            "a-slug",
        ]
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        addons.flyout_sorting = ADDONS_FLYOUT_SORTING_CALVER
        addons.flyout_sorting_latest_stable_at_beginning = True
        addons.save()
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        expected = [
            "latest",
            "stable",
            "2020.01.05",
            "z-slug",
            "a-slug",
            "2.0",
            "1.2",
            "1.12",
            "1.0",
        ]
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected

        addons.flyout_sorting_latest_stable_at_beginning = False
        addons.save()
        r = self.client.get(**kwargs)
        assert r.status_code == 200
        expected = [
            "2020.01.05",
            "z-slug",
            "stable",
            "latest",
            "a-slug",
            "2.0",
            "1.2",
            "1.12",
            "1.0",
        ]
        assert [v["slug"] for v in r.json()["versions"]["active"]] == expected
