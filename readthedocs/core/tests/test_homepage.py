import json
from pathlib import Path

import django_dynamic_fixture as fixture
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from readthedocs.core.views import schema


class HomepageTest(TestCase):

    def test_homepage_auth(self):
        user = fixture.get(
            User,
            username="user",
        )
        self.client.force_login(user)

        # Hitting "app.readthedocs.org" at /
        response = self.client.get(
            reverse("homepage"),
        )
        assert response.headers.get("Location") == reverse("projects_dashboard")

    def test_homepage_unauth(self):
        # Hitting "app.readthedocs.org" at /
        response = self.client.get(
            reverse("homepage"),
        )
        assert response.headers.get("Location") == reverse("account_login")

    def test_welcome_auth(self):
        user = fixture.get(
            User,
            username="user",
        )
        self.client.force_login(user)

        # Hitting "app.readthedocs.org" at /welcome
        response = self.client.get(
            reverse("welcome"),
        )
        assert response.headers.get("Location") == reverse("projects_dashboard")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_welcome_unauth(self):
        # Hitting "app.readthedocs.org" at /welcome
        response = self.client.get(
            reverse("welcome"),
        )
        assert response.headers.get("Location") == "https://about.readthedocs.com/?ref=readthedocs.org"

    def test_schema(self):
        response = self.client.get(reverse("schema"))
        assert response.status_code == 200
        assert response.headers.get("Content-Type") == "application/json"

        schema_path = (
            Path(settings.SITE_ROOT)
            / "readthedocs"
            / "rtd_tests"
            / "fixtures"
            / "spec"
            / "v2"
            / "schema.json"
        )
        with schema_path.open(encoding="utf-8") as schema_file:
            expected_schema = json.load(schema_file)

        assert response.json() == expected_schema

    def test_schema_is_login_exempt(self):
        assert schema.login_required is False
