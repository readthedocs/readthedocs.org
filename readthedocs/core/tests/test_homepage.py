from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase


class HomepageTest(TestCase):

    def test_homepage_auth(self):
        user = User(username="user")
        user.set_password("user")
        user.save()
        self.client.login(username="user", password="user")

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
        user = User(username="user")
        user.set_password("user")
        user.save()
        self.client.login(username="user", password="user")

        # Hitting "app.readthedocs.org" at /welcome
        response = self.client.get(
            reverse("welcome"),
        )
        assert response.headers.get("Location") == reverse("projects_dashboard")

    def test_welcome_unauth(self):
        # Hitting "app.readthedocs.org" at /welcome
        response = self.client.get(
            reverse("welcome"),
        )
        assert response.headers.get("Location") == "https://about.readthedocs.com/?ref=readthedocs.org"
