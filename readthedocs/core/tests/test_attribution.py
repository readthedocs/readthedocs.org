"""Tests for signup attribution capture and storage."""

import pytest
from django.contrib.auth.models import User

from readthedocs.core.middleware import AttributionMiddleware


SESSION_KEY = AttributionMiddleware.SESSION_KEY


class TestParseRef:
    def test_source_only(self):
        assert AttributionMiddleware.parse("hn") == {"source": "hn"}

    def test_all_parts(self):
        assert AttributionMiddleware.parse("newsletter/email/launch") == {
            "source": "newsletter",
            "medium": "email",
            "campaign": "launch",
        }

    def test_empty_parts_are_ignored(self):
        assert AttributionMiddleware.parse("newsletter//launch") == {
            "source": "newsletter",
            "campaign": "launch",
        }

    def test_extra_parts_stay_with_the_campaign(self):
        assert AttributionMiddleware.parse("a/b/c/d") == {
            "source": "a",
            "medium": "b",
            "campaign": "c/d",
        }

    def test_empty_ref(self):
        assert AttributionMiddleware.parse("") == {}
        assert AttributionMiddleware.parse("  ") == {}

    def test_long_parts_are_truncated(self):
        parsed = AttributionMiddleware.parse("x" * 500)
        assert len(parsed["source"]) == AttributionMiddleware.MAX_LENGTH


@pytest.mark.django_db
class TestAttributionMiddleware:
    def test_captures_ref(self, client):
        client.get("/", {"ref": "newsletter/email/launch"})

        assert client.session[SESSION_KEY] == {
            "source": "newsletter",
            "medium": "email",
            "campaign": "launch",
        }

    def test_first_touch_is_not_overwritten(self, client):
        client.get("/", {"ref": "first"})
        client.get("/", {"ref": "second"})

        assert client.session[SESSION_KEY] == {"source": "first"}

    def test_no_ref_stores_nothing(self, client):
        client.get("/")

        assert SESSION_KEY not in client.session

    def test_skips_authenticated_users(self, client):
        user = User.objects.create_user(username="test", password="test")
        client.force_login(user)

        client.get("/", {"ref": "hn"})

        assert SESSION_KEY not in client.session


@pytest.mark.django_db
class TestSignupAttribution:
    form_data = {
        "email": "test123@example.com",
        "username": "test123",
        "password1": "123456",
        "password2": "123456",
    }

    def test_signup_stores_attribution_on_profile(self, client):
        client.get("/", {"ref": "newsletter/email"})
        response = client.post("/accounts/signup/", data=self.form_data)
        assert response.status_code == 302

        profile = User.objects.get(username="test123").profile
        assert profile.attribution == {"source": "newsletter", "medium": "email"}
        assert profile.attribution_source == "newsletter"

        # The session data is consumed at signup.
        assert SESSION_KEY not in client.session

    def test_signup_without_attribution(self, client):
        response = client.post("/accounts/signup/", data=self.form_data)
        assert response.status_code == 302

        profile = User.objects.get(username="test123").profile
        assert profile.attribution == {}
        assert profile.attribution_source == ""
