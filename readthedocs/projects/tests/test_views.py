from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.integrations.models import Integration
from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization
from readthedocs.projects.constants import (
    DOWNLOADABLE_MEDIA_TYPES,
    MEDIA_TYPE_HTMLZIP,
    PUBLIC,
)
from readthedocs.projects.models import Project


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
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


@override_settings(RTD_ALLOW_ORGANIZATIONS=True)
class TestExternalBuildOptionWithOrganizations(TestExternalBuildOption):
    def setUp(self):
        super().setUp()
        self.organization = get(
            Organization,
            projects=[self.project],
            owners=[self.user],
        )


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestProjectUsersViews(TestCase):
    def setUp(self):
        self.user = get(User)
        get(EmailAddress, email=self.user.email, user=self.user, verified=True)
        self.project = get(Project, users=[self.user])
        self.another_user = get(User)
        get(
            EmailAddress,
            email=self.another_user.email,
            user=self.another_user,
            verified=True,
        )

    def test_invite_by_username(self):
        url = reverse("projects_users", args=[self.project.slug])
        self.client.force_login(self.user)
        resp = self.client.post(
            url,
            data={
                "username_or_email": self.another_user.username,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn(self.another_user, self.project.users.all())

        invitation = Invitation.objects.for_object(self.project).get()
        self.assertFalse(invitation.expired)
        self.assertEqual(invitation.object, self.project)
        self.assertEqual(invitation.from_user, self.user)
        self.assertEqual(invitation.to_user, self.another_user)
        self.assertEqual(invitation.to_email, None)

    def test_invite_by_email(self):
        url = reverse("projects_users", args=[self.project.slug])
        self.client.force_login(self.user)
        resp = self.client.post(
            url,
            data={
                "username_or_email": self.another_user.email,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn(self.another_user, self.project.users.all())

        invitation = Invitation.objects.for_object(self.project).get()
        self.assertFalse(invitation.expired)
        self.assertEqual(invitation.object, self.project)
        self.assertEqual(invitation.from_user, self.user)
        self.assertEqual(invitation.to_user, self.another_user)
        self.assertEqual(invitation.to_email, None)

    def test_invite_existing_maintainer_by_username(self):
        self.project.users.add(self.another_user)
        url = reverse("projects_users", args=[self.project.slug])
        self.client.force_login(self.user)
        resp = self.client.post(
            url,
            data={
                "username_or_email": self.another_user.username,
            },
        )
        self.assertEqual(resp.status_code, 200)
        form = resp.context_data["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("is already a maintainer", form.errors["username_or_email"][0])
        self.assertFalse(Invitation.objects.for_object(self.project).exists())

    def test_invite_existing_maintainer_by_email(self):
        self.project.users.add(self.another_user)
        url = reverse("projects_users", args=[self.project.slug])
        self.client.force_login(self.user)
        resp = self.client.post(
            url,
            data={
                "username_or_email": self.another_user.email,
            },
        )
        self.assertEqual(resp.status_code, 200)
        form = resp.context_data["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("is already a maintainer", form.errors["username_or_email"][0])
        self.assertFalse(Invitation.objects.for_object(self.project).exists())

    def test_invite_unknown_user(self):
        url = reverse("projects_users", args=[self.project.slug])
        self.client.force_login(self.user)
        resp = self.client.post(
            url,
            data={
                "username_or_email": "foobar",
            },
        )
        self.assertEqual(resp.status_code, 200)
        form = resp.context_data["form"]
        self.assertFalse(form.is_valid())
        self.assertIn("does not exist", form.errors["username_or_email"][0])
        self.assertNotIn(self.another_user, self.project.users.all())
        self.assertFalse(Invitation.objects.for_object(self.project).exists())

    def test_delete_maintainer(self):
        self.project.users.add(self.another_user)
        url = reverse("projects_users_delete", args=[self.project.slug])
        self.client.force_login(self.user)
        resp = self.client.post(
            url,
            data={
                "username": self.user.username,
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn(self.user, self.project.users.all())

    def test_delete_last_maintainer(self):
        url = reverse("projects_users_delete", args=[self.project.slug])
        self.client.force_login(self.user)
        resp = self.client.post(
            url,
            data={
                "username": self.user.username,
            },
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn(self.user, self.project.users.all())


@override_settings(RTD_ALLOW_ORGANIZATIONS=False)
class TestProjectDownloads(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, slug="project", users=[self.user])
        self.version = self.project.versions.first()
        self.version.privacy_level = PUBLIC
        self.version.save()

    def test_download_files(self):
        for type_ in DOWNLOADABLE_MEDIA_TYPES:
            resp = self.client.get(
                reverse(
                    "project_download_media",
                    args=[self.project.slug, type_, self.version.slug],
                ),
                headers={"host": "project.dev.readthedocs.io"},
            )
            self.assertEqual(resp.status_code, 200)
            extension = "zip" if type_ == MEDIA_TYPE_HTMLZIP else type_
            self.assertEqual(
                resp["X-Accel-Redirect"],
                f"/proxito/media/{type_}/project/latest/project.{extension}",
            )
