"""Serving docs of organizations that have been disabled for a long time."""

from datetime import timedelta

import django_dynamic_fixture as fixture
import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django_dynamic_fixture import get
from djstripe import models as djstripe
from djstripe.enums import SubscriptionStatus

from readthedocs.builds.constants import LATEST
from readthedocs.organizations.models import Organization
from readthedocs.payments.tests.utils import PaymentMixin
from readthedocs.projects.constants import PUBLIC
from readthedocs.projects.models import Project


@pytest.mark.proxito
@override_settings(
    PYTHON_MEDIA=False,
    PUBLIC_DOMAIN="dev.readthedocs.io",
    RTD_ALLOW_ORGANIZATIONS=True,
)
class TestDisabledOrganizationServing(PaymentMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.eric = fixture.get(User, username="eric")
        self.project = fixture.get(
            Project,
            slug="project",
            privacy_level=PUBLIC,
            external_builds_privacy_level=PUBLIC,
            users=[self.eric],
            main_language_project=None,
        )
        self.project.versions.update(privacy_level=PUBLIC, built=True, active=True)
        self.version = self.project.versions.get(slug=LATEST)
        self.host = "project.dev.readthedocs.io"

    def _create_organization(self, subscription_ended_days_ago, disabled):
        stripe_subscription = get(
            djstripe.Subscription,
            customer=get(djstripe.Customer),
            status=SubscriptionStatus.canceled,
            ended_at=timezone.now() - timedelta(days=subscription_ended_days_ago),
        )
        return get(
            Organization,
            disabled=disabled,
            projects=[self.project],
            stripe_subscription=stripe_subscription,
            stripe_customer=stripe_subscription.customer,
        )

    def test_serving_disabled_organization_docs(self):
        self._create_organization(subscription_ended_days_ago=100, disabled=True)

        resp = self.client.get("/en/latest/index.html", headers={"host": self.host})

        assert resp.status_code == 404
        assert "errors/proxito/organization_disabled.html" in [
            template.name for template in resp.templates
        ]
        # The response is purged from the CDN when the project is built again.
        assert resp.headers["CDN-Cache-Control"] == "public"

    def test_serving_recently_disabled_organization_docs(self):
        self._create_organization(subscription_ended_days_ago=35, disabled=True)

        resp = self.client.get("/en/latest/index.html", headers={"host": self.host})

        assert resp.status_code == 200
        assert resp["x-accel-redirect"] == "/proxito/media/html/project/latest/index.html"

    def test_serving_enabled_organization_docs(self):
        self._create_organization(subscription_ended_days_ago=100, disabled=False)

        resp = self.client.get("/en/latest/index.html", headers={"host": self.host})

        assert resp.status_code == 200
        assert resp["x-accel-redirect"] == "/proxito/media/html/project/latest/index.html"

    @override_settings(RTD_ALLOW_ORGANIZATIONS=False)
    def test_serving_disabled_organization_docs_without_organizations(self):
        self._create_organization(subscription_ended_days_ago=100, disabled=True)

        resp = self.client.get("/en/latest/index.html", headers={"host": self.host})

        assert resp.status_code == 200
        assert resp["x-accel-redirect"] == "/proxito/media/html/project/latest/index.html"

    def test_downloading_disabled_organization_docs(self):
        self._create_organization(subscription_ended_days_ago=100, disabled=True)

        resp = self.client.get("/_/downloads/en/latest/pdf/", headers={"host": self.host})

        assert resp.status_code == 404
        assert "errors/proxito/organization_disabled.html" in [
            template.name for template in resp.templates
        ]

    def test_downloading_enabled_organization_docs(self):
        self._create_organization(subscription_ended_days_ago=100, disabled=False)

        resp = self.client.get("/_/downloads/en/latest/pdf/", headers={"host": self.host})

        assert resp.status_code == 200
        assert (
            resp["x-accel-redirect"]
            == "/proxito/media/pdf/project/latest/project.pdf"
        )
