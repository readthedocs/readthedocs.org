from unittest import mock

import requests_mock
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.notifications.models import Notification
from readthedocs.oauth.constants import GITHUB, GITHUB_APP
from readthedocs.oauth.migrate import InstallationTargetGroup, MigrationTarget, GitHubAccountTarget
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)
from readthedocs.oauth.notifications import (
    MESSAGE_OAUTH_DEPLOY_KEY_NOT_REMOVED,
    MESSAGE_OAUTH_WEBHOOK_NOT_REMOVED,
)
from readthedocs.oauth.services.github import GitHubService
from readthedocs.organizations.models import Organization
from readthedocs.projects.models import Project


@override_settings(GITHUB_APP_NAME="readthedocs")
class TestMigrateToGitHubAppView(TestCase):
    def setUp(self):
        self.user = get(User)
        self.social_account_github = get(
            SocialAccount,
            provider=GitHubProvider.id,
            user=self.user,
            uid="1234",
            extra_data={"login": "user"},
        )
        get(
            SocialToken,
            account=self.social_account_github,
        )
        self.social_account_github_app = get(
            SocialAccount,
            provider=GitHubAppProvider.id,
            user=self.user,
            uid="1234",
            extra_data={"login": "user"},
        )
        self.github_app_installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=int(self.social_account_github_app.uid),
            target_type=GitHubAccountType.USER,
        )

        # Project with remote repository where the user is admin.
        self.remote_repository_a = get(
            RemoteRepository,
            name="repo-a",
            full_name="user/repo-a",
            html_url="https://github.com/user/repo-a",
            remote_id="1111",
            vcs_provider=GITHUB,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_account_github,
            remote_repository=self.remote_repository_a,
            admin=True,
        )
        self.project_with_remote_repository = get(
            Project,
            users=[self.user],
            remote_repository=self.remote_repository_a,
        )

        # Project with remote repository where the user is not admin.
        self.remote_repository_b = get(
            RemoteRepository,
            name="repo-b",
            full_name="user/repo-b",
            html_url="https://github.com/user/repo-b",
            remote_id="2222",
            vcs_provider=GITHUB,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_account_github,
            remote_repository=self.remote_repository_b,
            admin=False,
        )
        self.project_with_remote_repository_no_admin = get(
            Project,
            users=[self.user],
            remote_repository=self.remote_repository_b,
        )

        # Project with remote repository where the user doesn't have permissions at all.
        self.remote_repository_c = get(
            RemoteRepository,
            name="repo-c",
            full_name="user2/repo-c",
            html_url="https://github.com/user2/repo-c",
            remote_id="3333",
            vcs_provider=GITHUB,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_account_github,
            remote_repository=self.remote_repository_c,
            admin=False,
        )
        self.project_with_remote_repository_no_member = get(
            Project,
            users=[self.user],
            remote_repository=self.remote_repository_c,
        )

        # Project connected to a remote repository that belongs to an organization.
        self.remote_organization = get(
            RemoteOrganization,
            slug="org",
            name="Organization",
            remote_id="9999",
            vcs_provider=GITHUB,
        )
        get(
            RemoteOrganizationRelation,
            user=self.user,
            account=self.social_account_github,
        )
        self.remote_repository_d = get(
            RemoteRepository,
            name="repo-d",
            full_name="org/repo-d",
            html_url="https://github.com/org/repo-d",
            remote_id="4444",
            organization=self.remote_organization,
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_account_github,
            remote_repository=self.remote_repository_d,
            admin=True,
        )
        self.project_with_remote_organization = get(
            Project,
            users=[self.user],
            remote_repository=self.remote_repository_d,
        )
        self.github_app_organization_installation = get(
            GitHubAppInstallation,
            installation_id=2222,
            target_id=int(self.remote_organization.remote_id),
            target_type=GitHubAccountType.ORGANIZATION,
        )

        # Project without a remote repository.
        self.project_without_remote_repository = get(
            Project,
            users=[self.user],
            repo="https://github.com/user/repo-e",
        )

        # Make tests work on .com.
        if settings.RTD_ALLOW_ORGANIZATIONS:
            self.organization = get(
                Organization,
                owners=[self.user],
                projects=[
                    self.project_with_remote_repository,
                    self.project_with_remote_repository_no_admin,
                    self.project_with_remote_repository_no_member,
                    self.project_with_remote_organization,
                    self.project_without_remote_repository,
                ],
            )

        self.url = reverse("migrate_to_github_app")
        self.client.force_login(self.user)

    def _create_github_app_remote_repository(self, remote_repository):
        new_remote_repository = get(
            RemoteRepository,
            name=remote_repository.name,
            full_name=remote_repository.full_name,
            html_url=remote_repository.html_url,
            remote_id=remote_repository.remote_id,
            vcs_provider=GITHUB_APP,
            github_app_installation=self.github_app_installation,
        )
        if remote_repository.organization:
            new_remote_repository.organization = get(
                RemoteOrganization,
                slug=remote_repository.organization.slug,
                name=remote_repository.organization.name,
                remote_id=remote_repository.organization.remote_id,
                vcs_provider=GITHUB_APP,
            )
            new_remote_repository.github_app_installation = (
                self.github_app_organization_installation
            )
            new_remote_repository.save()
        for relation in remote_repository.remote_repository_relations.all():
            github_app_account = relation.user.socialaccount_set.get(
                provider=GitHubAppProvider.id
            )
            get(
                RemoteRepositoryRelation,
                user=relation.user,
                account=github_app_account,
                remote_repository=new_remote_repository,
                admin=relation.admin,
            )
        return new_remote_repository

    def test_user_without_github_account(self):
        self.user.socialaccount_set.all().delete()
        response = self.client.get(self.url)
        assert response.status_code == 302
        response = self.client.get(reverse("projects_dashboard"))
        content = response.content.decode()
        print(content)
        assert (
            "You don\\u0026#x27\\u003Bt have any GitHub account connected." in content
        )

    def test_user_without_github_account_but_with_github_app_account(self):
        self.user.socialaccount_set.exclude(provider=GitHubAppProvider.id).delete()
        response = self.client.get(self.url)
        assert response.status_code == 302
        response = self.client.get(reverse("projects_dashboard"))
        assert (
            "You have already migrated your account to the new GitHub App"
            in response.content.decode()
        )

    @requests_mock.Mocker(kw="request")
    def test_migration_page_initial_state(self, request):
        request.get("https://api.github.com/user", status_code=200)

        self.user.socialaccount_set.filter(provider=GitHubAppProvider.id).delete()
        response = self.client.get(self.url)
        assert response.status_code == 200
        context = response.context

        assert context["step"] == "overview"
        assert context["step_connect_completed"] is False
        assert list(context["migrated_projects"]) == []
        assert (
            context["old_application_link"]
            == "https://github.com/settings/connections/applications/123"
        )
        assert context["step_revoke_completed"] is False
        assert list(context["old_github_accounts"]) == [self.social_account_github]
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "install"})
        assert response.status_code == 200
        context = response.context
        assert context["installation_target_groups"] == [
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.social_account_github.uid),
                    login="user",
                    type=GitHubAccountType.USER,
                    avatar_url=self.social_account_github.get_avatar_url(),
                    profile_url=self.social_account_github.get_profile_url(),
                ),
                repository_ids={1111, 2222, 3333},
            ),
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.remote_organization.remote_id),
                    login="org",
                    type=GitHubAccountType.ORGANIZATION,
                    avatar_url=self.remote_organization.avatar_url,
                    profile_url=self.remote_organization.url,
                ),
                repository_ids={4444},
            ),
        ]
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "migrate"})
        assert response.status_code == 200
        context = response.context
        assert context["migration_targets"] == [
            MigrationTarget(
                project=self.project_with_remote_repository,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_admin,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_member,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_organization,
                has_installation=False,
                is_admin=False,
                target_id=int(self.remote_organization.remote_id),
            ),
        ]
        assert "installation_target_groups" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "revoke"})
        assert response.status_code == 200
        context = response.context
        assert context["has_projects_pending_migration"] is True
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context

    @requests_mock.Mocker(kw="request")
    def test_migration_page_step_connect_done(self, request):
        request.get("https://api.github.com/user", status_code=200)
        response = self.client.get(self.url)
        assert response.status_code == 200
        context = response.context

        assert context["step"] == "overview"
        assert context["step_connect_completed"] is True
        assert list(context["migrated_projects"]) == []
        assert (
            context["old_application_link"]
            == "https://github.com/settings/connections/applications/123"
        )
        assert context["step_revoke_completed"] is False
        assert list(context["old_github_accounts"]) == [self.social_account_github]
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "install"})
        assert response.status_code == 200
        context = response.context
        assert context["installation_target_groups"] == [
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.social_account_github.uid),
                    login="user",
                    type=GitHubAccountType.USER,
                    avatar_url=self.social_account_github.get_avatar_url(),
                    profile_url=self.social_account_github.get_profile_url(),
                ),
                repository_ids={1111, 2222, 3333},
            ),
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.remote_organization.remote_id),
                    login="org",
                    type=GitHubAccountType.ORGANIZATION,
                    avatar_url=self.remote_organization.avatar_url,
                    profile_url=self.remote_organization.url,
                ),
                repository_ids={4444},
            ),
        ]
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "migrate"})
        assert response.status_code == 200
        context = response.context
        assert context["migration_targets"] == [
            MigrationTarget(
                project=self.project_with_remote_repository,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_admin,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_member,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_organization,
                has_installation=False,
                is_admin=False,
                target_id=int(self.remote_organization.remote_id),
            ),
        ]
        assert "installation_target_groups" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "revoke"})
        assert response.status_code == 200
        context = response.context
        assert context["has_projects_pending_migration"] is True
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context

    @requests_mock.Mocker(kw="request")
    def test_migration_page_step_install_done(self, request):
        request.get("https://api.github.com/user", status_code=200)

        self._create_github_app_remote_repository(self.remote_repository_a)
        self._create_github_app_remote_repository(self.remote_repository_b)
        self._create_github_app_remote_repository(self.remote_repository_d)

        response = self.client.get(self.url)
        assert response.status_code == 200
        context = response.context

        assert context["step"] == "overview"
        assert context["step_connect_completed"] is True
        assert list(context["migrated_projects"]) == []
        assert (
            context["old_application_link"]
            == "https://github.com/settings/connections/applications/123"
        )
        assert context["step_revoke_completed"] is False
        assert list(context["old_github_accounts"]) == [self.social_account_github]
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "install"})
        assert response.status_code == 200
        context = response.context
        assert context["installation_target_groups"] == [
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.social_account_github.uid),
                    login="user",
                    type=GitHubAccountType.USER,
                    avatar_url=self.social_account_github.get_avatar_url(),
                    profile_url=self.social_account_github.get_profile_url(),
                ),
                repository_ids={3333},
            ),
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.remote_organization.remote_id),
                    login="org",
                    type=GitHubAccountType.ORGANIZATION,
                    avatar_url=self.remote_organization.avatar_url,
                    profile_url=self.remote_organization.url,
                ),
                repository_ids=set(),
            ),
        ]
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "migrate"})
        assert response.status_code == 200
        context = response.context
        assert context["migration_targets"] == [
            MigrationTarget(
                project=self.project_with_remote_repository,
                has_installation=True,
                is_admin=True,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_admin,
                has_installation=True,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_member,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_organization,
                has_installation=True,
                is_admin=True,
                target_id=int(self.remote_organization.remote_id),
            ),
        ]
        assert "installation_target_groups" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "revoke"})
        assert response.status_code == 200
        context = response.context
        assert context["has_projects_pending_migration"] is True
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context

    @requests_mock.Mocker(kw="request")
    @mock.patch.object(GitHubService, "remove_webhook")
    @mock.patch.object(GitHubService, "remove_ssh_key")
    def test_migration_page_step_migrate_one_project(
        self, remove_ssh_key, remove_webhook, request
    ):
        request.get("https://api.github.com/user", status_code=200)

        remove_ssh_key.return_value = True
        remove_webhook.return_value = True

        self._create_github_app_remote_repository(self.remote_repository_a)
        self._create_github_app_remote_repository(self.remote_repository_b)
        self._create_github_app_remote_repository(self.remote_repository_d)

        response = self.client.post(
            self.url, data={"project": self.project_with_remote_repository.slug}
        )
        assert response.status_code == 302
        response = self.client.get(self.url)
        assert response.status_code == 200
        context = response.context

        assert context["step"] == "overview"
        assert context["step_connect_completed"] is True
        assert list(context["migrated_projects"]) == [
            self.project_with_remote_repository,
        ]
        assert (
            context["old_application_link"]
            == "https://github.com/settings/connections/applications/123"
        )
        assert context["step_revoke_completed"] is False
        assert list(context["old_github_accounts"]) == [self.social_account_github]
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "install"})
        assert response.status_code == 200
        context = response.context
        assert context["installation_target_groups"] == [
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.social_account_github.uid),
                    login="user",
                    type=GitHubAccountType.USER,
                    avatar_url=self.social_account_github.get_avatar_url(),
                    profile_url=self.social_account_github.get_profile_url(),
                ),
                repository_ids={3333},
            ),
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.remote_organization.remote_id),
                    login="org",
                    type=GitHubAccountType.ORGANIZATION,
                    avatar_url=self.remote_organization.avatar_url,
                    profile_url=self.remote_organization.url,
                ),
                repository_ids=set(),
            ),
        ]
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "migrate"})
        assert response.status_code == 200
        context = response.context
        assert context["migration_targets"] == [
            MigrationTarget(
                project=self.project_with_remote_repository_no_admin,
                has_installation=True,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_member,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_organization,
                has_installation=True,
                is_admin=True,
                target_id=int(self.remote_organization.remote_id),
            ),
        ]
        assert "installation_target_groups" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "revoke"})
        assert response.status_code == 200
        context = response.context
        assert context["has_projects_pending_migration"] is True
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context

    @requests_mock.Mocker(kw="request")
    @mock.patch.object(GitHubService, "remove_webhook")
    @mock.patch.object(GitHubService, "remove_ssh_key")
    def test_migration_page_step_migrate_all_projects(
        self, remove_ssh_key, remove_webhook, request
    ):
        request.get("https://api.github.com/user", status_code=200)

        remove_ssh_key.return_value = True
        remove_webhook.return_value = True

        self._create_github_app_remote_repository(self.remote_repository_a)
        self._create_github_app_remote_repository(self.remote_repository_b)
        self._create_github_app_remote_repository(self.remote_repository_d)

        response = self.client.post(self.url)
        assert response.status_code == 302
        response = self.client.get(self.url)
        context = response.context

        assert context["step"] == "overview"
        assert context["step_connect_completed"] is True
        assert list(context["migrated_projects"]) == [
            self.project_with_remote_repository,
            self.project_with_remote_organization,
        ]
        assert (
            context["old_application_link"]
            == "https://github.com/settings/connections/applications/123"
        )
        assert context["step_revoke_completed"] is False
        assert list(context["old_github_accounts"]) == [self.social_account_github]
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "install"})
        context = response.context
        assert context["installation_target_groups"] == [
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.social_account_github.uid),
                    login="user",
                    type=GitHubAccountType.USER,
                    avatar_url=self.social_account_github.get_avatar_url(),
                    profile_url=self.social_account_github.get_profile_url(),
                ),
                repository_ids={3333},
            ),
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.remote_organization.remote_id),
                    login="org",
                    type=GitHubAccountType.ORGANIZATION,
                    avatar_url=self.remote_organization.avatar_url,
                    profile_url=self.remote_organization.url,
                ),
                repository_ids=set(),
            ),
        ]
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "migrate"})
        assert response.status_code == 200
        context = response.context
        assert context["migration_targets"] == [
            MigrationTarget(
                project=self.project_with_remote_repository_no_admin,
                has_installation=True,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_member,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
        ]
        assert "installation_target_groups" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "revoke"})
        assert response.status_code == 200
        context = response.context
        assert context["has_projects_pending_migration"] is True
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context

    @requests_mock.Mocker(kw="request")
    @mock.patch.object(GitHubService, "remove_webhook")
    @mock.patch.object(GitHubService, "remove_ssh_key")
    def test_migration_page_step_migrate_one_project_with_errors(
        self, remove_ssh_key, remove_webhook, request
    ):
        request.get("https://api.github.com/user", status_code=200)

        remove_ssh_key.return_value = False
        remove_webhook.return_value = False

        self._create_github_app_remote_repository(self.remote_repository_a)
        self._create_github_app_remote_repository(self.remote_repository_b)
        self._create_github_app_remote_repository(self.remote_repository_d)

        response = self.client.post(
            self.url, data={"project": self.project_with_remote_repository.slug}
        )
        assert response.status_code == 302
        response = self.client.get(self.url)
        context = response.context

        assert context["step"] == "overview"
        assert context["step_connect_completed"] is True
        assert list(context["migrated_projects"]) == [
            self.project_with_remote_repository,
        ]
        assert (
            context["old_application_link"]
            == "https://github.com/settings/connections/applications/123"
        )
        assert context["step_revoke_completed"] is False
        assert list(context["old_github_accounts"]) == [self.social_account_github]

        notifications = Notification.objects.for_user(self.user, self.user)
        assert notifications.count() == 2
        assert notifications.filter(
            message_id=MESSAGE_OAUTH_WEBHOOK_NOT_REMOVED
        ).exists()
        assert notifications.filter(
            message_id=MESSAGE_OAUTH_DEPLOY_KEY_NOT_REMOVED
        ).exists()
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "install"})
        assert response.status_code == 200
        context = response.context
        assert context["installation_target_groups"] == [
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.social_account_github.uid),
                    login="user",
                    type=GitHubAccountType.USER,
                    avatar_url=self.social_account_github.get_avatar_url(),
                    profile_url=self.social_account_github.get_profile_url(),
                ),
                repository_ids={3333},
            ),
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.remote_organization.remote_id),
                    login="org",
                    type=GitHubAccountType.ORGANIZATION,
                    avatar_url=self.remote_organization.avatar_url,
                    profile_url=self.remote_organization.url,
                ),
                repository_ids=set(),
            ),
        ]
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "migrate"})
        assert response.status_code == 200
        context = response.context
        assert context["migration_targets"] == [
            MigrationTarget(
                project=self.project_with_remote_repository_no_admin,
                has_installation=True,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_member,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_organization,
                has_installation=True,
                is_admin=True,
                target_id=int(self.remote_organization.remote_id),
            ),
        ]
        assert "installation_target_groups" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "revoke"})
        assert response.status_code == 200
        context = response.context
        assert context["has_projects_pending_migration"] is True
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context

    @requests_mock.Mocker(kw="request")
    def test_migration_page_step_revoke_done(self, request):
        request.get("https://api.github.com/user", status_code=401)
        response = self.client.get(self.url)
        assert response.status_code == 200
        context = response.context

        assert context["step"] == "overview"
        assert context["step_connect_completed"] is True
        assert list(context["migrated_projects"]) == []
        assert (
            context["old_application_link"]
            == "https://github.com/settings/connections/applications/123"
        )
        assert context["step_revoke_completed"] is True
        assert list(context["old_github_accounts"]) == [self.social_account_github]
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "install"})
        assert response.status_code == 200
        context = response.context
        assert context["installation_target_groups"] == [
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.social_account_github.uid),
                    login="user",
                    type=GitHubAccountType.USER,
                    avatar_url=self.social_account_github.get_avatar_url(),
                    profile_url=self.social_account_github.get_profile_url(),
                ),
                repository_ids={1111, 2222, 3333},
            ),
            InstallationTargetGroup(
                target=GitHubAccountTarget(
                    id=int(self.remote_organization.remote_id),
                    login="org",
                    type=GitHubAccountType.ORGANIZATION,
                    avatar_url=self.remote_organization.avatar_url,
                    profile_url=self.remote_organization.url,
                ),
                repository_ids={4444},
            ),
        ]
        assert "migration_targets" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "migrate"})
        assert response.status_code == 200
        context = response.context
        assert context["migration_targets"] == [
            MigrationTarget(
                project=self.project_with_remote_repository,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_admin,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_repository_no_member,
                has_installation=False,
                is_admin=False,
                target_id=int(self.social_account_github.uid),
            ),
            MigrationTarget(
                project=self.project_with_remote_organization,
                has_installation=False,
                is_admin=False,
                target_id=int(self.remote_organization.remote_id),
            ),
        ]
        assert "installation_target_groups" not in context
        assert "has_projects_pending_migration" not in context

        response = self.client.get(self.url, data={"step": "revoke"})
        assert response.status_code == 200
        context = response.context
        assert context["has_projects_pending_migration"] is True
        assert "installation_target_groups" not in context
        assert "migration_targets" not in context
