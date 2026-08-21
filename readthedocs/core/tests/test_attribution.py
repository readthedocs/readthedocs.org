"""Tests for first-touch attribution capture and storage at signup."""

import pytest
from django.contrib.auth.models import User

from readthedocs.core.middleware import FirstTouchAttributionMiddleware


SESSION_KEY = FirstTouchAttributionMiddleware.SESSION_KEY


@pytest.mark.django_db
class TestFirstTouchAttributionMiddleware:
    def test_captures_utm_parameters(self, client):
        client.get(
            "/",
            {
                "utm_source": "newsletter",
                "utm_medium": "email",
                "utm_campaign": "launch",
            },
        )

        data = client.session.get(SESSION_KEY)
        assert data["utm_source"] == "newsletter"
        assert data["utm_medium"] == "email"
        assert data["utm_campaign"] == "launch"
        assert data["landing_page"] == "/"
        assert data["first_touch_date"]

    def test_captures_external_referrer(self, client):
        client.get("/", HTTP_REFERER="https://news.ycombinator.com/item?id=1")

        data = client.session.get(SESSION_KEY)
        assert data["referrer"] == "https://news.ycombinator.com/item?id=1"

    def test_ignores_internal_referrer(self, client):
        client.get("/", HTTP_REFERER="http://testserver/projects/")

        assert SESSION_KEY not in client.session

    def test_ref_parameter_wins_over_referrer_header(self, client):
        client.get(
            "/",
            {"ref": "about.readthedocs.com"},
            HTTP_REFERER="http://testserver/projects/",
        )

        data = client.session.get(SESSION_KEY)
        assert data["referrer"] == "about.readthedocs.com"

    def test_first_touch_is_not_overwritten(self, client):
        client.get("/", {"utm_source": "first"})
        client.get("/", {"utm_source": "second", "utm_medium": "email"})

        data = client.session.get(SESSION_KEY)
        assert data["utm_source"] == "first"
        assert "utm_medium" not in data

    def test_no_signal_stores_nothing(self, client):
        client.get("/")

        assert SESSION_KEY not in client.session

    def test_skips_authenticated_users(self, client):
        user = User.objects.create_user(username="test", password="test")
        client.force_login(user)

        client.get("/", {"utm_source": "newsletter"})

        assert SESSION_KEY not in client.session

    def test_skips_api_requests(self, client):
        client.get(
            "/api/v2/",
            {"utm_source": "newsletter"},
            HTTP_REFERER="https://example.com/docs/",
        )

        assert SESSION_KEY not in client.session

    def test_skips_non_get_requests(self, client):
        client.post("/", {"utm_source": "newsletter"})

        assert SESSION_KEY not in client.session

    def test_truncates_long_values(self, client):
        client.get("/", {"utm_source": "x" * 1000})

        data = client.session.get(SESSION_KEY)
        assert len(data["utm_source"]) == 512


@pytest.mark.django_db
class TestSignupAttribution:
    form_data = {
        "email": "test123@example.com",
        "username": "test123",
        "password1": "123456",
        "password2": "123456",
    }

    def test_signup_stores_attribution_on_profile(self, client):
        client.get(
            "/",
            {"utm_source": "newsletter", "utm_campaign": "launch"},
            HTTP_REFERER="https://news.ycombinator.com/",
        )
        response = client.post("/accounts/signup/", data=self.form_data)
        assert response.status_code == 302

        profile = User.objects.get(username="test123").profile
        assert profile.attribution_utm_source == "newsletter"
        assert profile.attribution_utm_campaign == "launch"
        assert profile.attribution_utm_medium == ""
        assert profile.attribution_referrer == "https://news.ycombinator.com/"
        assert profile.attribution_landing_page == "/"
        assert profile.attribution_first_touch_date is not None

        # The session data is consumed at signup.
        assert SESSION_KEY not in client.session

    def test_signup_without_attribution(self, client):
        response = client.post("/accounts/signup/", data=self.form_data)
        assert response.status_code == 302

        profile = User.objects.get(username="test123").profile
        assert profile.attribution_utm_source == ""
        assert profile.attribution_referrer == ""
        assert profile.attribution_first_touch_date is None
