"""Tests for operations views."""

import django_dynamic_fixture as fixture
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class OperationsViewTest(TestCase):
    """Test operations views for Sentry and New Relic."""

    def setUp(self):
        """Set up test users."""
        self.staff_user = fixture.get(User, username="staff", is_staff=True)
        self.normal_user = fixture.get(User, username="normal", is_staff=False)

    def test_sentry_view_requires_authentication(self):
        """Test that anonymous users cannot access Sentry operations view."""
        response = self.client.get(reverse("operations_sentry"))
        # Should return 403 Forbidden for anonymous users
        assert response.status_code == 403
        data = response.json()
        assert "error" in data

    def test_sentry_view_requires_staff(self):
        """Test that normal users cannot access Sentry operations view."""
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse("operations_sentry"))
        # Should return 403 Forbidden
        assert response.status_code == 403

    def test_sentry_view_staff_access(self):
        """Test that staff users can access Sentry operations view."""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("operations_sentry"))
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "sentry"
        assert "sentry" in data["message"]

    def test_newrelic_view_requires_authentication(self):
        """Test that anonymous users cannot access New Relic operations view."""
        response = self.client.get(reverse("operations_newrelic"))
        # Should return 403 Forbidden for anonymous users
        assert response.status_code == 403
        data = response.json()
        assert "error" in data

    def test_newrelic_view_requires_staff(self):
        """Test that normal users cannot access New Relic operations view."""
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse("operations_newrelic"))
        # Should return 403 Forbidden
        assert response.status_code == 403

    def test_newrelic_view_staff_access(self):
        """Test that staff users can access New Relic operations view."""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse("operations_newrelic"))
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "newrelic"
        assert "newrelic" in data["message"]

    def test_sentry_view_generates_log_messages(self):
        """Test that Sentry operations view generates log messages."""
        self.client.force_login(self.staff_user)
        with self.assertLogs("readthedocs.core.views", level="INFO") as logs:
            response = self.client.get(reverse("operations_sentry"))
            assert response.status_code == 200
            # Check that both info and error logs were generated
            log_output = "\n".join(logs.output)
            assert "sentry logging check" in log_output
            assert "sentry error logging check" in log_output
            # Check that both INFO and ERROR levels were used
            assert any("INFO" in log for log in logs.output)
            assert any("ERROR" in log for log in logs.output)

    def test_newrelic_view_generates_log_messages(self):
        """Test that New Relic operations view generates log messages."""
        self.client.force_login(self.staff_user)
        with self.assertLogs("readthedocs.core.views", level="INFO") as logs:
            response = self.client.get(reverse("operations_newrelic"))
            assert response.status_code == 200
            # Check that both info and error logs were generated
            log_output = "\n".join(logs.output)
            assert "newrelic logging check" in log_output
            assert "newrelic error logging check" in log_output
            # Check that both INFO and ERROR levels were used
            assert any("INFO" in log for log in logs.output)
            assert any("ERROR" in log for log in logs.output)
