from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.integrations.models import Integration
from readthedocs.projects.models import Project


class TestExternalBuildOption(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=[self.user])
        self.integration = get(
            Integration,
            integration_type=Integration.GITHUB_WEBHOOK,
            project=self.project,
        )
        self.url = reverse("projects_advanced", args=[self.project.slug])
        self.client.force_login(self.user)

    def test_unsuported_integration(self):
        self.integration.delete()
        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertTrue(field.disabled)
        self.assertTrue(
            field.help_text.startswith(
                "To build from pull requests you need a GitHub or GitLab"
            )
        )

        get(
            Integration,
            project=self.project,
            integration_type=Integration.BITBUCKET_WEBHOOK,
        )
        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertTrue(field.disabled)
        self.assertTrue(
            field.help_text.startswith(
                "To build from pull requests you need a GitHub or GitLab"
            )
        )

    def test_github_integration(self):
        self.integration.provider_data = {}
        self.integration.save()

        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertFalse(field.disabled)
        self.assertTrue(field.help_text.startswith("More information in"))

        self.integration.provider_data = {"events": ["pull_request"]}
        self.integration.save()
        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertFalse(field.disabled)
        self.assertTrue(field.help_text.startswith("More information in"))

        self.integration.provider_data = {"events": []}
        self.integration.save()
        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertTrue(field.disabled)
        self.assertTrue(
            field.help_text.startswith(
                "To build from pull requests your repository's webhook needs to send pull request events."
            )
        )

    def test_gitlab_integration(self):
        self.integration.integration_type = Integration.GITLAB_WEBHOOK
        self.integration.provider_data = {}
        self.integration.save()

        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertFalse(field.disabled)
        self.assertTrue(field.help_text.startswith("More information in"))

        self.integration.provider_data = {"merge_requests_events": True}
        self.integration.save()
        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertFalse(field.disabled)
        self.assertTrue(field.help_text.startswith("More information in"))

        self.integration.provider_data = {"merge_requests_events": False}
        self.integration.save()
        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        self.assertTrue(field.disabled)
        self.assertTrue(
            field.help_text.startswith(
                "To build from pull requests your repository's webhook needs to send pull request events."
            )
        )
