"""Test hosting views."""

import django_dynamic_fixture as fixture
import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from readthedocs.builds.constants import EXTERNAL, INTERNAL, LATEST
from readthedocs.builds.models import Build
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project


@override_settings(
    PUBLIC_DOMAIN="dev.readthedocs.io",
    PUBLIC_DOMAIN_USES_HTTPS=True,
    GLOBAL_ANALYTICS_CODE=None,
)
@pytest.mark.proxito
class TestReadTheDocsConfigJson(TestCase):
    def setUp(self):
        self.user = fixture.get(User, username="user")
        self.user.set_password("user")
        self.user.save()

        self.project = fixture.get(
            Project,
            slug="project",
            language="en",
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
            repo="git://10.10.0.1/project",
            programming_language="words",
            single_version=False,
            users=[self.user],
            main_language_project=None,
        )
        self.project.versions.update(
            privacy_level=PUBLIC,
            built=True,
            active=True,
            type=INTERNAL,
            identifier="1a2b3c",
        )
        self.version = self.project.versions.get(slug=LATEST)
        self.build = fixture.get(
            Build,
            version=self.version,
        )

    def test_get_config(self):
        r = self.client.get(
            reverse("proxito_readthedocs_config_json"),
            {"url": "https://project.dev.readthedocs.io/en/latest/"},
            secure=True,
            HTTP_HOST="project.dev.readthedocs.io",
        )
        assert r.status_code == 200

        expected = {
            "comment": "THIS RESPONSE IS IN ALPHA FOR TEST PURPOSES ONLY AND IT'S GOING TO CHANGE COMPLETELY -- DO NOT USE IT!",
            "project": {
                "slug": self.project.slug,
                "language": self.project.language,
                "repository_url": self.project.repo,
                "programming_language": self.project.programming_language,
            },
            "version": {
                "slug": self.version.slug,
                "external": self.version.type == EXTERNAL,
            },
            "build": {
                "id": self.build.pk,
            },
            "domains": {
                "dashboard": settings.PRODUCTION_DOMAIN,
            },
            "readthedocs": {
                "analytics": {
                    "code": None,
                }
            },
            "features": {
                "analytics": {
                    "code": None,
                },
                "external_version_warning": {
                    "enabled": True,
                    "query_selector": "[role=main]",
                },
                "non_latest_version_warning": {
                    "enabled": True,
                    "query_selector": "[role=main]",
                    "versions": [
                        "latest",
                    ],
                },
                "doc_diff": {
                    "enabled": True,
                    "base_url": "https://project.dev.readthedocs.io/en/latest/index.html",
                    "root_selector": "[role=main]",
                    "inject_styles": True,
                    "base_host": "",
                    "base_page": "",
                },
                "flyout": {
                    "translations": [],
                    "versions": [
                        {"slug": "latest", "url": "/en/latest/"},
                    ],
                    "downloads": [],
                    "vcs": {
                        "url": "https://github.com",
                        "username": "readthedocs",
                        "repository": "test-builds",
                        "branch": self.version.identifier,
                        "filepath": "/docs/index.rst",
                    },
                },
                "search": {
                    "api_endpoint": "/_/api/v3/search/",
                    "default_filter": "subprojects:project/latest",
                    "filters": [
                        ["Search only in this project", "project:project/latest"],
                        ["Search subprojects", "subprojects:project/latest"],
                    ],
                    "project": "project",
                    "version": "latest",
                },
            },
        }
        assert r.json() == expected
