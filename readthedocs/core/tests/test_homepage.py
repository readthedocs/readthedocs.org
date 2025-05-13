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
        assert response.headers.get("Location") == reverse("projects_dashboard")

    @override_settings(PRODUCTION_DOMAIN="readthedocs.org")
    def test_welcome_unauth(self):
        # Hitting "app.readthedocs.org" at /welcome
        response = self.client.get(
            reverse("welcome"),
        )
        assert response.headers.get("Location") == "https://about.readthedocs.com/?ref=readthedocs.org"
