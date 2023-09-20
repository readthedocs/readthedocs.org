"""Test hosting views."""

import json
from pathlib import Path

import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from readthedocs.builds.constants import LATEST
from readthedocs.builds.models import Build
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project


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
            single_version=False,
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
