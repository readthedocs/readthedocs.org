"""Tests for signup attribution capture and storage."""

import pytest
from django.contrib.auth.models import User

from readthedocs.core.middleware import AttributionMiddleware


SESSION_KEY = AttributionMiddleware.SESSION_KEY


@pytest.mark.django_db
class TestAttributionMiddleware:
    def test_captures_attribution_parameters(self, client):
        client.get(
            "/",
            {"utm_source": "newsletter", "utm_medium": "email", "ref": "hn"},
        )

        assert client.session[SESSION_KEY] == {
            "utm_source": "newsletter",
            "utm_medium": "email",
            "ref": "hn",
        }

    def test_ignores_unknown_parameters(self, client):
        client.get("/", {"utm_source": "newsletter", "utm_term": "docs"})

        assert client.session[SESSION_KEY] == {"utm_source": "newsletter"}

    def test_first_touch_is_not_overwritten(self, client):
        client.get("/", {"utm_source": "first"})
        client.get("/", {"utm_source": "second", "utm_medium": "email"})

        assert client.session[SESSION_KEY] == {"utm_source": "first"}

    def test_no_parameters_stores_nothing(self, client):
        client.get("/")

        assert SESSION_KEY not in client.session

    def test_skips_authenticated_users(self, client):
        user = User.objects.create_user(username="test", password="test")
        client.force_login(user)

        client.get("/", {"utm_source": "newsletter"})

        assert SESSION_KEY not in client.session

    def test_truncates_long_values(self, client):
        client.get("/", {"utm_source": "x" * 1000})

        assert len(client.session[SESSION_KEY]["utm_source"]) == 255


@pytest.mark.django_db
class TestSignupAttribution:
    form_data = {
        "email": "test123@example.com",
        "username": "test123",
        "password1": "123456",
        "password2": "123456",
    }

    def test_signup_stores_attribution_on_profile(self, client):
        client.get("/", {"utm_source": "newsletter", "ref": "hn"})
        response = client.post("/accounts/signup/", data=self.form_data)
        assert response.status_code == 302

        profile = User.objects.get(username="test123").profile
        assert profile.attribution == {"utm_source": "newsletter", "ref": "hn"}
        assert profile.attribution_source == "newsletter"

        # The session data is consumed at signup.
        assert SESSION_KEY not in client.session

    def test_signup_without_attribution(self, client):
        response = client.post("/accounts/signup/", data=self.form_data)
        assert response.status_code == 302

        profile = User.objects.get(username="test123").profile
        assert profile.attribution == {}
        assert profile.attribution_source == ""

    def test_attribution_source_falls_back_to_referrer(self, client):
        client.get("/", {"ref": "hn"})
        client.post("/accounts/signup/", data=self.form_data)

        profile = User.objects.get(username="test123").profile
        assert profile.attribution_source == "hn"
