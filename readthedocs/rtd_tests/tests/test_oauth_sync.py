import django_dynamic_fixture as fixture
import requests_mock
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.models import (
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)
from django_dynamic_fixture import get
from allauth.socialaccount.providers.gitlab.provider import GitLabProvider
from readthedocs.oauth.services import GitHubService
from readthedocs.projects.models import Project


class GitHubOAuthSyncTests(TestCase):
    payload_user_repos = [
        {
            "id": 11111,
            "node_id": "a1b2c3",
            "name": "repository",
            "full_name": "organization/repository",
            "private": False,
            "owner": {
                "login": "organization",
                "id": 11111,
                "node_id": "a1b2c3",
                "avatar_url": "https://avatars3.githubusercontent.com/u/11111?v=4",
                "gravatar_id": "",
                "url": "https://api.github.com/users/organization",
                "type": "User",
                "site_admin": False,
            },
            "html_url": "https://github.com/organization/repository",
            "description": "",
            "fork": True,
            "url": "https://api.github.com/repos/organization/repository",
            "created_at": "2019-06-14T14:11:29Z",
            "updated_at": "2019-06-15T15:05:33Z",
            "pushed_at": "2019-06-15T15:11:19Z",
            "git_url": "git://github.com/organization/repository.git",
            "ssh_url": "git@github.com:organization/repository.git",
            "clone_url": "https://github.com/organization/repository.git",
            "svn_url": "https://github.com/organization/repository",
            "homepage": None,
            "language": "Python",
            "archived": False,
            "disabled": False,
            "open_issues_count": 0,
            "default_branch": "master",
            "permissions": {
                "admin": False,
                "push": True,
                "pull": True,
            },
        }
    ]

    def setUp(self):
        self.user = fixture.get(User)
        self.socialaccount = fixture.get(
            SocialAccount,
            user=self.user,
            provider=GitHubProvider.id,
        )
        self.token = fixture.get(
            SocialToken,
            account=self.socialaccount,
        )
        self.service = list(GitHubService.for_user(self.user))[0]

    @requests_mock.Mocker(kw="mock_request")
    def test_sync_delete_stale(self, mock_request):
        mock_request.get(
            "https://api.github.com/user/repos", json=self.payload_user_repos
        )
        mock_request.get("https://api.github.com/user/orgs", json=[])

        repo_1 = fixture.get(
            RemoteRepository,
            full_name="organization/repository",
            remote_id="11111",
            vcs_provider=GITHUB,
        )
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=repo_1,
            user=self.user,
            account=self.socialaccount,
        )

        repo_2 = fixture.get(
            RemoteRepository,
            full_name="organization/old-repository",
            remote_id="64789",
            vcs_provider=GITHUB,
        )
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=repo_2,
            user=self.user,
            account=self.socialaccount,
        )

        # RemoteRepositoryRelation with RemoteRepository
        # linked to a Project should also be removed
        project = fixture.get(Project)
        repo_3 = fixture.get(
            RemoteRepository,
            full_name="organization/project-linked-repository",
            remote_id="54321",
            vcs_provider=GITHUB,
        )
        repo_3.projects.add(project)
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=repo_3,
            user=self.user,
            account=self.socialaccount,
        )

        # Project from another provider (GitLab) that has the same ID should not be removed.
        gitlab_socialaccount = fixture.get(
            SocialAccount,
            user=self.user,
            provider=GitLabProvider.id,
        )
        gitlab_repo = fixture.get(
            RemoteRepository,
            full_name="user/repo",
            remote_id=repo_3.remote_id,
            vcs_provider=GitLabProvider.id,
        )
        fixture.get(
            RemoteRepositoryRelation,
            remote_repository=gitlab_repo,
            user=self.user,
            account=gitlab_socialaccount,
        )

        org = fixture.get(
            RemoteOrganization,
            name="organization",
        )
        fixture.get(
            RemoteOrganizationRelation,
            remote_organization=org,
            user=self.user,
            account=self.socialaccount,
        )

        self.assertEqual(RemoteRepository.objects.count(), 4)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 4)
        self.assertEqual(RemoteOrganization.objects.count(), 1)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 1)

        assert self.socialaccount.remote_repository_relations.count() == 3
        assert self.socialaccount.remote_organization_relations.count() == 1

        self.service.sync()

        # After calling .sync, old-repository remote relation should be deleted,
        # project-linked-repository remote relation should be conserved,
        # and only the one's returned by the API should be present (organization/repository)
        self.assertEqual(RemoteRepository.objects.count(), 4)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 2)
        self.assertTrue(
            RemoteRepository.objects.filter(
                full_name="organization/repository"
            ).exists()
        )
        self.assertTrue(
            RemoteRepository.objects.filter(
                full_name="organization/project-linked-repository"
            ).exists()
        )
        self.assertEqual(RemoteOrganization.objects.count(), 1)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 0)

        assert self.socialaccount.remote_repository_relations.count() == 1
        assert self.socialaccount.remote_organization_relations.count() == 0

    @requests_mock.Mocker(kw="mock_request")
    def test_sync_repositories(self, mock_request):
        mock_request.get(
            "https://api.github.com/user/repos", json=self.payload_user_repos
        )

        self.assertEqual(RemoteRepository.objects.count(), 0)
        self.assertEqual(RemoteOrganization.objects.count(), 0)

        repository_remote_ids = self.service.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(RemoteOrganization.objects.count(), 0)
        self.assertEqual(len(repository_remote_ids), 1)

        remote_repository = RemoteRepository.objects.first()
        self.assertEqual(repository_remote_ids[0], remote_repository.remote_id)
        self.assertEqual(remote_repository.full_name, "organization/repository")
        self.assertEqual(remote_repository.name, "repository")
        self.assertFalse(remote_repository.remote_repository_relations.first().admin)
        self.assertFalse(remote_repository.private)

    @requests_mock.Mocker(kw="mock_request")
    def test_sync_repositories_relation_with_organization(self, mock_request):
        """
        Sync repositories relations for a user where the RemoteRepository and RemoteOrganization already exist.

        Note that ``repository.owner.type == 'Organization'`` in the GitHub response.
        """
        self.payload_user_repos[0]["owner"]["type"] = "Organization"
        mock_request.get(
            "https://api.github.com/user/repos", json=self.payload_user_repos
        )

        self.assertEqual(RemoteRepository.objects.count(), 0)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 0)
        self.assertEqual(RemoteOrganization.objects.count(), 0)

        remote_organization = fixture.get(
            RemoteOrganization,
            remote_id=11111,
            slug="organization",
            vcs_provider="github",
        )
        remote_repository = fixture.get(
            RemoteRepository,
            remote_id=11111,
            organization=remote_organization,
            vcs_provider="github",
        )
        repository_remote_ids = self.service.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 1)
        self.assertEqual(RemoteOrganization.objects.count(), 1)

        self.assertEqual(len(repository_remote_ids), 1)
        remote_repository = RemoteRepository.objects.first()
        self.assertEqual(repository_remote_ids[0], remote_repository.remote_id)
        self.assertEqual(remote_repository.full_name, "organization/repository")
        self.assertEqual(remote_repository.name, "repository")
        self.assertEqual(remote_repository.organization.slug, "organization")
        self.assertFalse(remote_repository.remote_repository_relations.first().admin)
        self.assertFalse(remote_repository.private)

    @requests_mock.Mocker(kw="mock_request")
    def test_sync_repositories_moved_from_org_to_user(self, mock_request):
        """
        Sync repositories for a repo that was part of a GH organization and was moved to a GH user.

        Note that ``repository.owner.type == 'User'`` in the GitHub response.
        """
        mock_request.get(
            "https://api.github.com/user/repos", json=self.payload_user_repos
        )

        self.assertEqual(RemoteRepository.objects.count(), 0)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 0)
        self.assertEqual(RemoteOrganization.objects.count(), 0)

        remote_organization = fixture.get(
            RemoteOrganization,
            remote_id=11111,
            slug="organization",
            vcs_provider="github",
        )
        remote_repository = fixture.get(
            RemoteRepository,
            remote_id=11111,
            organization=remote_organization,
            vcs_provider="github",
        )
        repository_remote_ids = self.service.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 1)
        self.assertEqual(RemoteOrganization.objects.count(), 1)

        self.assertEqual(len(repository_remote_ids), 1)
        remote_repository = RemoteRepository.objects.first()
        self.assertEqual(repository_remote_ids[0], remote_repository.remote_id)
        self.assertEqual(remote_repository.full_name, "organization/repository")
        self.assertEqual(remote_repository.name, "repository")
        self.assertIsNone(remote_repository.organization)
        self.assertFalse(remote_repository.remote_repository_relations.first().admin)
        self.assertFalse(remote_repository.private)

    @requests_mock.Mocker(kw="mock_request")
    def test_sync_repositories_only_creates_one_remote_repo_per_vcs_repo(
        self, mock_request
    ):
        mock_request.get(
            "https://api.github.com/user/repos", json=self.payload_user_repos
        )

        self.assertEqual(RemoteRepository.objects.count(), 0)

        remote_repositories = self.service.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(len(remote_repositories), 1)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 1)

        user_2 = fixture.get(User)
        user_2_socialaccount = fixture.get(
            SocialAccount,
            user=user_2,
            provider=GitHubProvider.id,
        )
        fixture.get(
            SocialToken,
            account=user_2_socialaccount,
        )

        service_2 = GitHubService(user=user_2, account=user_2_socialaccount)
        remote_repositories = service_2.sync_repositories()

        self.assertEqual(RemoteRepository.objects.count(), 1)
        self.assertEqual(len(remote_repositories), 1)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 2)

    @requests_mock.Mocker(kw="mock_request")
    def test_sync_organizations(self, mock_request):
        payload = [
            {
                "login": "readthedocs",
                "id": 11111,
                "node_id": "a1b2c3",
                "url": "https://api.github.com/orgs/organization",
                "avatar_url": "https://avatars2.githubusercontent.com/u/11111?v=4",
                "description": "",
            }
        ]
        mock_request.get("https://api.github.com/user/orgs", json=payload)

        payload = {
            "login": "organization",
            "id": 11111,
            "node_id": "a1b2c3",
            "url": "https://api.github.com/orgs/organization",
            "avatar_url": "https://avatars2.githubusercontent.com/u/11111?v=4",
            "description": "",
            "name": "Organization",
            "company": None,
            "blog": "http://organization.org",
            "location": "Portland, Oregon & Worldwide. ",
            "email": None,
            "is_verified": False,
            "html_url": "https://github.com/organization",
            "created_at": "2010-08-16T19:17:46Z",
            "updated_at": "2020-08-12T14:26:39Z",
            "type": "Organization",
        }
        mock_request.get("https://api.github.com/orgs/organization", json=payload)

        self.assertEqual(RemoteRepository.objects.count(), 0)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 0)
        self.assertEqual(RemoteOrganization.objects.count(), 0)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 0)

        organization_remote_ids, repository_remote_ids = self.service.sync_organizations()

        self.assertEqual(RemoteRepository.objects.count(), 0)
        self.assertEqual(RemoteRepositoryRelation.objects.count(), 0)
        self.assertEqual(RemoteOrganization.objects.count(), 1)
        self.assertEqual(RemoteOrganizationRelation.objects.count(), 1)
        self.assertEqual(len(organization_remote_ids), 1)
        self.assertEqual(len(repository_remote_ids), 0)
        remote_organization = RemoteOrganization.objects.first()
        self.assertEqual(organization_remote_ids[0], remote_organization.remote_id)
