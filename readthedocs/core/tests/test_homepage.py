import django_dynamic_fixture as fixture
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase, override_settings


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
        assert response.status_code == 302
        assert response.headers.get("Location") == reverse("projects_dashboard")
        self._assert_never_cached(response)

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_welcome_unauth(self):
        # Hitting "app.readthedocs.org" at /welcome
        response = self.client.get(
            reverse("welcome"),
        )
        # Permanent for search engines, but never cached by browsers or the CDN,
        # so the same URL still sends the user to the dashboard once they log in.
        assert response.status_code == 301
        assert response.headers.get("Location") == "https://about.readthedocs.com/?ref=readthedocs.org"
        self._assert_never_cached(response)

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_welcome_unauth_keeps_query_string(self):
        response = self.client.get(reverse("welcome") + "?utm_source=test")
        assert response.status_code == 301
        assert (
            response.headers.get("Location")
            == "https://about.readthedocs.com/?ref=readthedocs.org&utm_source=test"
        )

    def _assert_never_cached(self, response):
        assert "no-store" in response.headers["Cache-Control"]
        assert "private" in response.headers["Cache-Control"]
        assert response.headers["CDN-Cache-Control"] == "private"
        assert "Cookie" in response.headers["Vary"]
