from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from unittest import mock
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.integrations.models import Integration
from readthedocs.invitations.models import Invitation
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAppInstallation, RemoteRepository
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
        self.url = reverse("projects_edit", args=[self.project.slug])
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

    def test_github_app_integration(self):
        Integration.objects.all().delete()
        github_app_installation = get(
            GitHubAppInstallation,
        )
        remote_repository = get(
            RemoteRepository,
            vcs_provider=GITHUB_APP,
            github_app_installation=github_app_installation,
        )
        self.project.remote_repository = remote_repository
        self.project.save()

        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_enabled"]
        assert not field.disabled
        assert field.help_text.startswith("More information in")

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

    @override_settings(ALLOW_PRIVATE_REPOS=True)
    def test_privacy_level_pr_previews_match_remote_repository_if_public(self):
        remote_repository = get(RemoteRepository, private=False)
        self.project.remote_repository = remote_repository
        self.project.save()

        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_privacy_level"]
        self.assertTrue(field.disabled)
        self.assertIn("We have detected that this project is public", field.help_text)
        self.assertEqual(self.project.external_builds_privacy_level, PUBLIC)

        remote_repository.private = True
        remote_repository.save()
        self.project.save()

        resp = self.client.get(self.url)
        field = resp.context["form"].fields["external_builds_privacy_level"]
        self.assertFalse(field.disabled)
        self.assertEqual(self.project.external_builds_privacy_level, PUBLIC)


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
        url = reverse("projects_users_create", args=[self.project.slug])
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
        url = reverse("projects_users_create", args=[self.project.slug])
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
        url = reverse("projects_users_create", args=[self.project.slug])
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
        url = reverse("projects_users_create", args=[self.project.slug])
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
        url = reverse("projects_users_create", args=[self.project.slug])
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

        # Ensure a message is shown
        messages = list(get_messages(resp.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "User deleted")

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


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
    ALLOW_PRIVATE_REPOS=False,
)
class TestProjectEditView(TestCase):
    def setUp(self):
        self.user = get(User)
        self.project = get(Project, slug="project", users=[self.user], repo="https://github.com/user/repo")
        self.url = reverse("projects_edit", args=[self.project.slug])
        self.client.force_login(self.user)

    @mock.patch("readthedocs.projects.forms.trigger_build")
    @mock.patch("readthedocs.projects.forms.index_project")
    def test_search_indexing_enabled(self, index_project, trigger_build):
        resp = self.client.get(self.url)
        assert resp.status_code == 200
        form = resp.context["form"]
        assert "search_indexing_enabled" not in form.fields

        self.project.search_indexing_enabled = False
        self.project.save()

        resp = self.client.get(self.url)
        assert resp.status_code == 200
        form = resp.context["form"]
        assert "search_indexing_enabled" in form.fields

        data = {
            "name": self.project.name,
            "repo": self.project.repo,
            "language": self.project.language,
            "default_version": self.project.default_version,
            "versioning_scheme": self.project.versioning_scheme,
        }

        data["search_indexing_enabled"] = False
        resp = self.client.post(
            self.url,
            data=data,
        )
        assert resp.status_code == 302
        self.project.refresh_from_db()
        assert not self.project.search_indexing_enabled
        index_project.delay.assert_not_called()

        data["search_indexing_enabled"] = True
        resp = self.client.post(
            self.url,
            data=data,
        )
        assert resp.status_code == 302
        self.project.refresh_from_db()
        assert self.project.search_indexing_enabled
        index_project.delay.assert_called_once_with(project_slug=self.project.slug)
