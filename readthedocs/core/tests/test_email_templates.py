"""Tests for rendering customer email templates."""

import datetime
from types import SimpleNamespace

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.test import override_settings
from django.urls import path
from django.utils import timezone


def unused_view(request, **kwargs):
    pass


urlpatterns = [
    path(
        "organizations/<slug:slug>/subscription/",
        unused_view,
        name="subscription_detail",
    ),
    path("pricing/", unused_view, name="pricing"),
    path("support/", unused_view, name="support"),
    path(
        "projects/<slug:project_slug>/domains/<int:pk>/",
        unused_view,
        name="projects_domains_edit",
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class EmailTemplateTests(SimpleTestCase):
    def test_trial_email_has_matching_content_and_links(self):
        context = {
            "organization": SimpleNamespace(name="Example <Docs>", slug="example"),
            "production_uri": "https://readthedocs.com",
        }
        html = render_to_string(
            "subscriptions/notifications/trial_ending_email.html", context
        )
        text = render_to_string(
            "subscriptions/notifications/trial_ending_email.txt", context
        )

        assert "Your trial is ending" in html
        assert "Example &lt;Docs&gt;" in html
        assert "Example <Docs>" in text
        assert 'alt="Read the Docs"' in html
        assert 'bgcolor="#00778e"' in html
        assert "Choose a subscription" in html
        for content in (html, text):
            assert "The Read the Docs team" in content
            assert "https://about.readthedocs.com" in content
            assert "less than 7 days" in content
            assert "builds and documentation serving will be disabled" in content
            assert (
                "https://readthedocs.com/organizations/example/subscription/" in content
            )
            assert "https://readthedocs.com/pricing/" in content
            assert "https://readthedocs.com/support/" in content

    def test_subscription_emails_have_primary_action(self):
        context = {
            "organization": SimpleNamespace(name="Example", slug="example"),
            "production_uri": "https://readthedocs.com",
        }
        for name, label in (
            ("trial_ending", "Choose a subscription"),
            ("subscription_required", "Choose a subscription"),
            ("subscription_ended", "Renew your subscription"),
            ("organization_disabled", "Renew your subscription"),
        ):
            html = render_to_string(
                f"subscriptions/notifications/{name}_email.html", context
            )
            assert 'bgcolor="#00778e"' in html
            assert label in html
            assert (
                'href="https://readthedocs.com/organizations/example/subscription/"'
                in html
            )

    def test_button_escapes_url_and_label(self):
        html = render_to_string(
            "core/email/button.html",
            {
                "action_url": 'https://example.com/?a=1&b="2"',
                "action_label": "Choose <plan>",
            },
        )
        assert 'href="https://example.com/?a=1&amp;b=&quot;2&quot;"' in html
        assert "Choose &lt;plan&gt;" in html

    def test_confirmation_email_escapes_dynamic_url(self):
        html = render_to_string(
            "account/email/email_confirmation_message.html",
            {"activate_url": "https://example.com/verify?token=1&next=2"},
        )

        assert "Verify your email address" in html
        assert "https://example.com/verify?token=1&amp;next=2" in html

    def test_domain_email_renders_both_validation_states(self):
        domain = SimpleNamespace(
            domain="docs.example.com",
            project=SimpleNamespace(slug="example"),
            pk=42,
            validation_process_expiration_date=timezone.now()
            + datetime.timedelta(days=2),
            validation_process_expired=False,
        )
        context = {"domain": domain, "production_uri": "https://readthedocs.org"}

        pending = render_to_string(
            "domains/notifications/pending_domain_configuration_email.html", context
        )
        domain.validation_process_expired = True
        expired = render_to_string(
            "domains/notifications/pending_domain_configuration_email.html", context
        )

        assert "stop trying to validate" in pending
        assert "validation period for this domain has ended" in expired
        for content in (pending, expired):
            assert "https://readthedocs.org/projects/example/domains/42/" in content
