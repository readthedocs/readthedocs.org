import copy
from unittest import mock

from allauth.socialaccount.providers.bitbucket_oauth2.provider import BitbucketOAuth2Provider
from allauth.socialaccount.providers.gitlab.provider import GitLabProvider
import requests_mock
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.builds.constants import (
    BUILD_STATUS_FAILURE,
    BUILD_STATUS_PENDING,
    BUILD_STATUS_SUCCESS,
    EXTERNAL,
    LATEST,
)
from readthedocs.builds.models import Build, Version
from readthedocs.integrations.models import GitHubAppIntegration
from readthedocs.integrations.models import GitHubWebhook, GitLabWebhook
from readthedocs.oauth.constants import BITBUCKET, GITHUB, GITHUB_APP, GITLAB
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)
from readthedocs.oauth.services import BitbucketService, GitHubService, GitLabService
from readthedocs.oauth.services.base import SyncServiceError
from readthedocs.oauth.services.githubapp import GitHubAppService
from readthedocs.projects import constants
from readthedocs.projects.models import Project


@override_settings(
    PRODUCTION_DOMAIN="readthedocs.org",
    PUBLIC_DOMAIN="readthedocs.io",
)
class GitHubAppTests(TestCase):
    def setUp(self):
        self.user = get(User)
        self.account = get(
            SocialAccount,
            uid="1111",
            user=self.user,
            provider=GitHubAppProvider.id,
        )
        get(
            SocialToken,
            account=self.account,
        )
        self.installation = get(
            GitHubAppInstallation,
            installation_id=1111,
            target_id=int(self.account.uid),
            target_type=GitHubAccountType.USER,
        )
        self.remote_repository = get(
            RemoteRepository,
            name="repo",
            full_name="user/repo",
            vcs_provider=GITHUB_APP,
            github_app_installation=self.installation,
            description="Some description",
        )
        get(
            RemoteRepositoryRelation,
            remote_repository=self.remote_repository,
            user=self.user,
            account=self.account,
            admin=True,
        )
        self.project = get(
            Project, users=[self.user], remote_repository=self.remote_repository
        )
        self.integration = get(
            GitHubAppIntegration,
            project=self.project,
        )

        self.remote_organization = get(
            RemoteOrganization,
            slug="org",
            remote_id="2222",
            vcs_provider=GITHUB_APP,
        )
        get(
            RemoteOrganizationRelation,
            remote_organization=self.remote_organization,
            user=self.user,
            account=self.account,
        )
        self.organization_installation = get(
            GitHubAppInstallation,
            installation_id=2222,
            target_id=int(self.remote_organization.remote_id),
            target_type=GitHubAccountType.ORGANIZATION,
        )
        self.remote_repository_with_org = get(
            RemoteRepository,
            name="repo",
            full_name="org/repo",
            vcs_provider=GITHUB_APP,
            github_app_installation=self.organization_installation,
            organization=self.remote_organization,
        )
        get(
            RemoteRepositoryRelation,
            remote_repository=self.remote_repository_with_org,
            user=self.user,
            account=self.account,
            admin=True,
        )
        self.project_with_org = get(
            Project,
            users=[self.user],
            remote_repository=self.remote_repository_with_org,
        )
        self.api_url = "https://api.github.com:443"

    def _merge_dicts(self, a, b):
        for k, v in b.items():
            if k in a and isinstance(a[k], dict):
                self._merge_dicts(a[k], v)
            else:
                a[k] = v

    def _get_access_token_json(self, **kwargs):
        default = {
            "token": "ghs_16C7e42F292c6912E7710c838347Ae178B4a",
            "expires_at": "2016-07-11T22:14:10Z",
            "permissions": {"issues": "write", "contents": "read"},
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_installation_json(self, id, **kwargs):
        default = {
            "id": id,
            "account": {
                "login": "user",
                "id": 1111,
                "type": "User",
            },
            "html_url": f"https://github.com/organizations/github/settings/installations/{id}",
            "app_id": 1,
            "target_id": 1111,
            "target_type": "User",
            "permissions": {"checks": "write", "metadata": "read", "contents": "read"},
            "events": ["push", "pull_request"],
            "repository_selection": "all",
            "created_at": "2017-07-08T16:18:44-04:00",
            "updated_at": "2017-07-08T16:18:44-04:00",
            "app_slug": "github-actions",
            "suspended_at": None,
            "suspended_by": None,
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_repository_json(self, full_name, **kwargs):
        user, repo = full_name.split("/")
        default = {
            "id": 1111,
            "name": repo,
            "full_name": full_name,
            "ssh_url": f"git@github.com:{full_name}.git",
            "clone_url": f"https://github.com/{full_name}.git",
            "html_url": f"https://github.com/{full_name}",
            "private": False,
            "default_branch": "main",
            "url": f"https://api.github.com/repos/{full_name}",
            "description": "Some description",
            "owner": {
                "login": user,
                "id": 1111,
                "type": "User",
                "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                "url": f"https://api.github.com/users/{user}",
            },
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_collaborator_json(self, **kwargs):
        default = {
            "id": 1111,
            "login": "user",
            "permissions": {"admin": True},
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_organization_json(self, **kwargs):
        default = {
            "login": "org",
            "id": 2222,
            "url": "https://api.github.com/orgs/org",
            "repos_url": "https://api.github.com/orgs/org/repos",
            "events_url": "https://api.github.com/orgs/org/events",
            "hooks_url": "https://api.github.com/orgs/org/hooks",
            "issues_url": "https://api.github.com/orgs/org/issues",
            "members_url": "https://api.github.com/orgs/org/members{/member}",
            "public_members_url": "https://api.github.com/orgs/org/public_members{/member}",
            "avatar_url": "https://github.com/images/error/octocat_happy.gif",
            "description": "Some organization",
            "name": "Organization",
            "email": "org@example.com",
            "html_url": "https://github.com/org",
            "created_at": "2008-01-14T04:33:35Z",
            "type": "Organization",
            "billing_email": "mona@github.com",
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_user_json(self, **kwargs):
        default = {
            "login": "user",
            "id": 1111,
            "type": "User",
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_commit_json(self, commit, **kwargs):
        default = {
            "url": f"https://api.github.com/repos/user/repo/commits/{commit}",
            "sha": commit,
            "html_url": f"https://github.com/user/repo/commit/{commit}",
            # "comments_url": "https://api.github.com/repos/octocat/Hello-World/commits/6dcb09b5b57875f334f61aebed695e2e4193db5e/comments",
            "commit": {
                "url": f"https://api.github.com/repos/octocat/Hello-World/git/commits/{commit}",
                "author": {
                    "name": "Monalisa Octocat",
                    "email": "mona@github.com",
                    "date": "2011-04-14T16:00:49Z",
                },
                "committer": {
                    "name": "Monalisa Octocat",
                    "email": "mona@github.com",
                    "date": "2011-04-14T16:00:49Z",
                },
                "message": "Fix all the bugs",
                "tree": {
                    "url": f"https://api.github.com/repos/user/repo/tree/{commit}",
                    "sha": commit,
                },
                "comment_count": 0,
            },
            "author": {
                "login": "octocat",
                "id": 1,
                "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                "gravatar_id": "",
                "url": "https://api.github.com/users/octocat",
                "html_url": "https://github.com/octocat",
                "type": "User",
                "site_admin": False,
            },
            "committer": {
                "login": "octocat",
                "id": 1,
                "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                "gravatar_id": "",
                "url": "https://api.github.com/users/octocat",
                "html_url": "https://github.com/octocat",
                "type": "User",
                "site_admin": False,
            },
            "parents": [
                {
                    "url": "https://api.github.com/repos/user/repo/commits/6dcb09b5b57875f334f61aebed695e2e4193db5e",
                    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
                }
            ],
            "stats": {"additions": 104, "deletions": 4, "total": 108},
            "files": [],
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_pull_request_json(self, number: int, repo_full_name, **kwargs):
        user, repo = repo_full_name.split("/")
        default = {
            "url": f"https://api.github.com/repos/{repo_full_name}/issues/{number}",
            "id": 1,
            "html_url": f"https://github.com/{repo_full_name}/pull/{number}",
            "comments_url": f"https://api.github.com/repos/{repo_full_name}/issues/{number}/comments",
            "number": number,
            "state": "open",
            "locked": False,
            "title": "Amazing new feature",
            "user": {
                "login": user,
                "id": 1,
                "url": f"https://api.github.com/users/{user}",
                "html_url": f"https://github.com/{user}",
                "type": "User",
            },
            "body": "Please pull these awesome changes in!",
            "labels": [],
            "milestone": None,
            "active_lock_reason": None,
            "created_at": "2011-01-26T19:01:12Z",
            "updated_at": "2011-01-26T19:01:12Z",
            "closed_at": None,
            "assignee": None,
            "assignees": [],
            "author_association": "OWNER",
            "draft": False,
        }
        self._merge_dicts(default, kwargs)
        return default

    def _get_comment_json(self, issue_number, repo_full_name, **kwargs):
        id = kwargs.get("id", 1)
        default = {
            "id": id,
            "node_id": "MDEyOklzc3VlQ29tbWVudDE=",
            "url": f"https://api.github.com/repos/{repo_full_name}/issues/comments/{id}",
            "html_url": f"https://github.com/{repo_full_name}/issues/{issue_number}#issuecomment-1",
            "body": "Comment",
            "user": {
                "login": "octocat",
                "id": 1,
                "url": "https://api.github.com/users/octocat",
                "html_url": "https://github.com/octocat",
                "type": "User",
            },
            "created_at": "2011-04-14T16:00:49Z",
            "updated_at": "2011-04-14T16:00:49Z",
            "issue_url": f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}",
            "author_association": "COLLABORATOR",
        }
        self._merge_dicts(default, kwargs)
        return default

    def test_for_project(self):
        services = list(GitHubAppService.for_project(self.project))
        assert len(services) == 1
        service = services[0]
        assert service.installation == self.installation

        services = list(GitHubAppService.for_project(self.project_with_org))
        assert len(services) == 1
        service = services[0]
        assert service.installation == self.organization_installation

    @requests_mock.Mocker(kw="request")
    def test_for_user(self, request):
        new_installation_id = 3333
        assert not GitHubAppInstallation.objects.filter(
            installation_id=new_installation_id
        ).exists()
        request.get(
            "https://api.github.com/user/installations",
            json={
                "installations": [
                    self._get_installation_json(
                        id=self.installation.installation_id,
                        account={"id": self.account.uid},
                    ),
                    self._get_installation_json(
                        id=new_installation_id,
                        target_id=2,
                        target_type="Organization",
                        account={"login": "octocat", "id": 2, "type": "Organization"},
                    ),
                ]
            },
        )
        services = list(GitHubAppService.for_user(self.user))
        assert len(services) == 2

        self.installation.refresh_from_db()
        assert self.installation.installation_id == 1111
        assert self.installation.target_id == int(self.account.uid)
        assert self.installation.target_type == GitHubAccountType.USER

        new_installation = GitHubAppInstallation.objects.get(
            installation_id=new_installation_id
        )
        assert new_installation.target_id == 2
        assert new_installation.target_type == GitHubAccountType.ORGANIZATION

    @requests_mock.Mocker(kw="request")
    @mock.patch.object(GitHubAppService, "sync")
    @mock.patch.object(GitHubAppService, "update_or_create_organization")
    @mock.patch.object(GitHubAppService, "update_or_create_repositories")
    def test_sync_user_access(
        self,
        update_or_create_repositories,
        update_or_create_organization,
        sync,
        request,
    ):
        request.get(
            "https://api.github.com/user/installations",
            json={
                "installations": [
                    self._get_installation_json(
                        id=self.installation.installation_id,
                        account={"id": self.account.uid},
                    ),
                ],
            },
        )

        GitHubAppService.sync_user_access(self.user)
        sync.assert_called_once()
        update_or_create_repositories.assert_has_calls(
            [
                mock.call([int(self.remote_repository.remote_id)]),
                mock.call([int(self.remote_repository_with_org.remote_id)]),
            ],
            any_order=True,
        )
        update_or_create_organization.assert_called_once_with(
            self.remote_organization.slug
        )

    @requests_mock.Mocker(kw="request")
    def test_create_repository(self, request):
        new_repo_id = 4444
        assert not RemoteRepository.objects.filter(
            remote_id=new_repo_id, vcs_provider=GitHubAppProvider.id
        ).exists()

        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/4444",
            json=self._get_repository_json(
                full_name="user/repo", id=4444, owner={"id": int(self.account.uid)}
            ),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/installation",
            json=self._get_installation_json(id=1111),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.update_or_create_repositories([new_repo_id])

        repo = RemoteRepository.objects.get(
            remote_id=new_repo_id, vcs_provider=GitHubAppProvider.id
        )
        assert repo.name == "repo"
        assert repo.full_name == "user/repo"
        assert repo.organization is None
        assert repo.description == "Some description"
        assert repo.avatar_url == "https://github.com/images/error/octocat_happy.gif"
        assert repo.ssh_url == "git@github.com:user/repo.git"
        assert repo.html_url == "https://github.com/user/repo"
        assert repo.clone_url == "https://github.com/user/repo.git"
        assert not repo.private
        assert repo.default_branch == "main"
        assert repo.github_app_installation == self.installation

        relations = repo.remote_repository_relations.all()
        assert relations.count() == 1
        relation = relations[0]
        assert relation.user == self.user
        assert relation.account == self.account
        assert relation.admin

    @requests_mock.Mocker(kw="request")
    def test_create_private_repository(self, request):
        new_repo_id = 4444
        assert not RemoteRepository.objects.filter(
            remote_id=new_repo_id, vcs_provider=GitHubAppProvider.id
        ).exists()

        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/4444",
            json=self._get_repository_json(
                full_name="user/repo",
                id=4444,
                owner={"id": int(self.account.uid)},
                private=True,
            ),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.update_or_create_repositories([new_repo_id])

        repo = RemoteRepository.objects.get(
            remote_id=new_repo_id, vcs_provider=GitHubAppProvider.id
        )
        assert repo.name == "repo"
        assert repo.full_name == "user/repo"
        assert repo.organization is None
        assert repo.description == "Some description"
        assert repo.avatar_url == "https://github.com/images/error/octocat_happy.gif"
        assert repo.ssh_url == "git@github.com:user/repo.git"
        assert repo.html_url == "https://github.com/user/repo"
        assert repo.clone_url == "https://github.com/user/repo.git"
        assert repo.private
        assert repo.default_branch == "main"
        assert repo.github_app_installation == self.installation

        relations = repo.remote_repository_relations.all()
        assert relations.count() == 1
        relation = relations[0]
        assert relation.user == self.user
        assert relation.account == self.account
        assert relation.admin

    @requests_mock.Mocker(kw="request")
    def test_update_repository(self, request):
        assert self.remote_repository.description == "Some description"
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}",
            json=self._get_repository_json(
                full_name="user/repo",
                id=int(self.remote_repository.remote_id),
                owner={"id": int(self.account.uid)},
                description="New description",
            ),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/installation",
            json=self._get_installation_json(id=1111),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.update_or_create_repositories([int(self.remote_repository.remote_id)])

        self.remote_repository.refresh_from_db()
        assert self.remote_repository.description == "New description"

    @requests_mock.Mocker(kw="request")
    def test_update_private_repository(self, request):
        assert self.remote_repository.description == "Some description"
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}",
            json=self._get_repository_json(
                full_name="user/repo",
                id=int(self.remote_repository.remote_id),
                owner={"id": int(self.account.uid)},
                description="New description",
                private=True,
            ),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.update_or_create_repositories([int(self.remote_repository.remote_id)])

        self.remote_repository.refresh_from_db()
        assert self.remote_repository.description == "New description"

    @requests_mock.Mocker(kw="request")
    def test_update_invalid_repository(self, request):
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}",
            status_code=404,
        )

        service = self.installation.service
        service.update_or_create_repositories([int(self.remote_repository.remote_id)])
        assert not RemoteRepository.objects.filter(
            id=self.remote_repository.id
        ).exists()

    @requests_mock.Mocker(kw="request")
    def test_sync(self, request):
        assert self.installation.repositories.count() == 1
        request.get(
            f"{self.api_url}/app/installations/1111",
            json=self._get_installation_json(id=1111),
        )
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/installation/repositories",
            json={
                "repositories": [
                    self._get_repository_json(
                        full_name="user/repo", id=int(self.remote_repository.remote_id)
                    ),
                    self._get_repository_json(full_name="user/repo2", id=2222),
                    self._get_repository_json(full_name="user/repo3", id=3333),
                ]
            },
        )

        request.get(
            f"{self.api_url}/repos/user/repo/collaborators",
            json=[self._get_collaborator_json()],
        )
        request.get(
            f"{self.api_url}/repos/user/repo2/collaborators",
            json=[self._get_collaborator_json()],
        )
        request.get(
            f"{self.api_url}/repos/user/repo3/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.sync()

        assert self.installation.repositories.count() == 3

        repo = self.installation.repositories.get(full_name="user/repo")
        assert repo.name == "repo"
        assert repo.remote_id == self.remote_repository.remote_id
        assert repo.default_branch == "main"
        assert repo.vcs_provider == GITHUB_APP
        assert repo.private is False
        assert repo.remote_repository_relations.count() == 1
        relation = repo.remote_repository_relations.first()
        assert relation.user == self.user
        assert relation.account == self.account
        assert relation.admin

        repo = self.installation.repositories.get(full_name="user/repo2")
        assert repo.name == "repo2"
        assert repo.remote_id == "2222"
        assert repo.remote_repository_relations.count() == 1
        assert repo.default_branch == "main"
        assert repo.vcs_provider == GITHUB_APP
        assert repo.private is False
        relation = repo.remote_repository_relations.first()
        assert relation.user == self.user
        assert relation.account == self.account
        assert relation.admin

        repo = self.installation.repositories.get(full_name="user/repo3")
        assert repo.name == "repo3"
        assert repo.remote_id == "3333"
        assert repo.remote_repository_relations.count() == 1
        assert repo.default_branch == "main"
        assert repo.vcs_provider == GITHUB_APP
        assert repo.private is False
        relation = repo.remote_repository_relations.first()
        assert relation.user == self.user
        assert relation.account == self.account
        assert relation.admin

    @requests_mock.Mocker(kw="request")
    def test_sync_delete_remote_repositories(self, request):
        assert self.installation.repositories.count() == 1
        request.get(
            f"{self.api_url}/app/installations/1111",
            json=self._get_installation_json(id=1111),
        )
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/installation/repositories",
            json={
                "repositories": [
                    self._get_repository_json(full_name="user/repo2", id=2222),
                ]
            },
        )
        request.get(
            f"{self.api_url}/repos/user/repo2/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.sync()

        assert self.installation.repositories.count() == 1
        repo = self.installation.repositories.get(full_name="user/repo2")
        assert repo.name == "repo2"
        assert repo.remote_id == "2222"
        assert repo.remote_repository_relations.count() == 1
        assert repo.default_branch == "main"
        assert repo.vcs_provider == GITHUB_APP
        assert repo.private is False
        relation = repo.remote_repository_relations.first()
        assert relation.user == self.user
        assert relation.account == self.account
        assert relation.admin

    @requests_mock.Mocker(kw="request")
    def test_sync_repositories_with_organization(self, request):
        assert self.organization_installation.repositories.count() == 1
        request.get(
            f"{self.api_url}/app/installations/{self.organization_installation.installation_id}",
            json=self._get_installation_json(
                id=self.organization_installation.installation_id,
                account={"id": 2222, "login": "org", "type": "Organization"},
                target_type="Organization",
                target_id=2222,
            ),
        )
        request.post(
            f"{self.api_url}/app/installations/{self.organization_installation.installation_id}/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/installation/repositories",
            json={
                "repositories": [
                    self._get_repository_json(
                        full_name="org/repo2",
                        id=2222,
                        owner={"id": 2222, "login": "org", "type": "Organization"},
                    ),
                ]
            },
        )
        request.get(
            f"{self.api_url}/repos/org/repo2/collaborators",
            json=[self._get_collaborator_json()],
        )
        request.get(
            f"{self.api_url}/orgs/org",
            json=self._get_organization_json(login="org", id=2222),
        )
        request.get(
            f"{self.api_url}/orgs/org/members",
            json=[self._get_user_json(id=1111, login="user")],
        )

        service = self.organization_installation.service
        service.sync()

        assert self.organization_installation.repositories.count() == 1
        repo = self.organization_installation.repositories.get(full_name="org/repo2")
        assert repo.name == "repo2"
        assert repo.remote_id == "2222"
        assert repo.remote_repository_relations.count() == 1
        assert repo.default_branch == "main"
        assert repo.vcs_provider == GITHUB_APP
        assert repo.private is False
        relation = repo.remote_repository_relations.first()
        assert relation.user == self.user
        assert relation.account == self.account
        assert relation.admin
        remote_organization = repo.organization
        assert remote_organization.slug == "org"
        assert remote_organization.remote_id == "2222"
        assert remote_organization.name == "Organization"
        assert remote_organization.email == "org@example.com"
        assert remote_organization.url == "https://github.com/org"
        assert (
            remote_organization.avatar_url
            == "https://github.com/images/error/octocat_happy.gif"
        )
        assert remote_organization.vcs_provider == GITHUB_APP

    @requests_mock.Mocker(kw="request")
    def test_sync_repo_moved_from_org_to_user(self, request):
        assert self.installation.repositories.count() == 1
        assert self.organization_installation.repositories.count() == 1
        assert self.remote_repository_with_org.organization == self.remote_organization
        assert (
            self.remote_repository_with_org.github_app_installation
            == self.organization_installation
        )

        request.get(
            f"{self.api_url}/app/installations/1111",
            json=self._get_installation_json(id=1111),
        )
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )

        request.get(
            f"{self.api_url}/installation/repositories",
            json={
                "repositories": [
                    self._get_repository_json(
                        full_name="user/repo", id=int(self.remote_repository.remote_id)
                    ),
                    self._get_repository_json(
                        full_name="user/repo2",
                        id=int(self.remote_repository_with_org.remote_id),
                    ),
                ]
            },
        )
        request.get(
            f"{self.api_url}/repos/user/repo/collaborators",
            json=[self._get_collaborator_json()],
        )
        request.get(
            f"{self.api_url}/repos/user/repo2/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.sync()
        assert self.installation.repositories.count() == 2
        assert self.organization_installation.repositories.count() == 0

        self.remote_repository_with_org.refresh_from_db()
        assert self.remote_repository_with_org.organization is None
        assert (
            self.remote_repository_with_org.github_app_installation == self.installation
        )
        assert self.remote_repository_with_org.name == "repo2"
        assert self.remote_repository_with_org.full_name == "user/repo2"

    @requests_mock.Mocker(kw="request")
    def test_sync_orphan_organization_is_deleted(self, request):
        assert self.organization_installation.repositories.count() == 1
        request.get(
            f"{self.api_url}/app/installations/{self.organization_installation.installation_id}",
            json=self._get_installation_json(
                id=self.organization_installation.installation_id,
                account={"id": 2222, "login": "org", "type": "Organization"},
                target_type="Organization",
                target_id=2222,
            ),
        )
        request.post(
            f"{self.api_url}/app/installations/{self.organization_installation.installation_id}/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/installation/repositories",
            json={"repositories": []},
        )

        service = self.organization_installation.service
        service.sync()

        assert self.organization_installation.repositories.count() == 0
        assert not RemoteOrganization.objects.filter(
            id=self.remote_organization.id
        ).exists()

    @requests_mock.Mocker(kw="request")
    def test_sync_with_uninstalled_installation(self, request):
        assert self.installation.repositories.count() == 1
        request.get(
            f"{self.api_url}/app/installations/1111",
            status_code=404,
        )
        service = self.installation.service
        with self.assertRaises(SyncServiceError):
            service.sync()

        assert not GitHubAppInstallation.objects.filter(
            id=self.installation.id
        ).exists()
        assert not RemoteRepository.objects.filter(
            id=self.remote_repository.id
        ).exists()

    @requests_mock.Mocker(kw="request")
    def test_sync_with_suspended_installation(self, request):
        assert self.installation.repositories.count() == 1
        request.get(
            f"{self.api_url}/app/installations/1111",
            json=self._get_installation_json(
                id=1111, suspended_at="2021-01-01T00:00:00Z"
            ),
        )
        service = self.installation.service
        with self.assertRaises(SyncServiceError):
            service.sync()

        assert not GitHubAppInstallation.objects.filter(
            id=self.installation.id
        ).exists()
        assert not RemoteRepository.objects.filter(
            id=self.remote_repository.id
        ).exists()

    @requests_mock.Mocker(kw="request")
    def test_send_build_status_pending(self, request):
        commit = "1234abc"
        version = self.project.versions.get(slug=LATEST)
        build = get(
            Build,
            project=self.project,
            version=version,
        )
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}/commits/{commit}",
            json=self._get_commit_json(commit=commit),
        )
        status_api_request = request.post(
            f"{self.api_url}/repos/user/repo/statuses/{commit}",
            json={},
        )

        service = self.installation.service
        assert service.send_build_status(
            build=build, commit=commit, status=BUILD_STATUS_PENDING
        )
        assert status_api_request.called
        assert status_api_request.last_request.json() == {
            "context": f"docs/readthedocs:{self.project.slug}",
            "description": "Read the Docs build is in progress!",
            "state": "pending",
            "target_url": f"https://readthedocs.org/projects/{self.project.slug}/builds/{build.pk}/",
        }

    @requests_mock.Mocker(kw="request")
    def test_send_build_status_success(self, request):
        commit = "1234abc"
        version = self.project.versions.get(slug=LATEST)
        version.built = True
        version.save()
        build = get(
            Build,
            project=self.project,
            version=version,
        )
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}/commits/{commit}",
            json=self._get_commit_json(commit=commit),
        )
        status_api_request = request.post(
            f"{self.api_url}/repos/user/repo/statuses/{commit}",
            json={},
        )

        service = self.installation.service
        assert service.send_build_status(
            build=build, commit=commit, status=BUILD_STATUS_SUCCESS
        )
        assert status_api_request.called
        assert status_api_request.last_request.json() == {
            "context": f"docs/readthedocs:{self.project.slug}",
            "description": "Read the Docs build succeeded!",
            "state": "success",
            "target_url": f"http://{self.project.slug}.readthedocs.io/en/latest/",
        }

    @requests_mock.Mocker(kw="request")
    def test_send_build_status_success_when_not_built(self, request):
        """Test that when status is SUCCESS but version is not built, it links to build detail page.

        This is specifically for external versions (PR builds) which are read-only and should
        always link to the build detail page when not built.
        """
        commit = "1234abc"
        # Create an external version (PR build) that is not built
        version = get(Version, project=self.project, type=EXTERNAL, built=False)
        build = get(
            Build,
            project=self.project,
            version=version,
        )
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}/commits/{commit}",
            json=self._get_commit_json(commit=commit),
        )
        status_api_request = request.post(
            f"{self.api_url}/repos/user/repo/statuses/{commit}",
            json={},
        )

        service = self.installation.service
        assert service.send_build_status(
            build=build, commit=commit, status=BUILD_STATUS_SUCCESS
        )
        assert status_api_request.called
        assert status_api_request.last_request.json() == {
            "context": f"docs/readthedocs:{self.project.slug}",
            "description": "Read the Docs build succeeded!",
            "state": "success",
            # Should link to build detail page, not version docs
            "target_url": f"https://readthedocs.org/projects/{self.project.slug}/builds/{build.pk}/",
        }

    @requests_mock.Mocker(kw="request")
    def test_send_build_status_failure(self, request):
        commit = "1234abc"
        version = self.project.versions.get(slug=LATEST)
        build = get(
            Build,
            project=self.project,
            version=version,
        )
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}/commits/{commit}",
            json=self._get_commit_json(commit=commit),
        )
        status_api_request = request.post(
            f"{self.api_url}/repos/user/repo/statuses/{commit}",
            json={},
        )

        service = self.installation.service
        assert service.send_build_status(
            build=build, commit=commit, status=BUILD_STATUS_FAILURE
        )
        assert status_api_request.called
        assert status_api_request.last_request.json() == {
            "context": f"docs/readthedocs:{self.project.slug}",
            "description": "Read the Docs build failed!",
            "state": "failure",
            "target_url": f"https://readthedocs.org/projects/{self.project.slug}/builds/{build.pk}/",
        }

    @requests_mock.Mocker(kw="request")
    def test_get_clone_token(self, request):
        token = "ghs_16C7e42F292c6912E7710c838347Ae178B4a"
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(toke=token),
        )
        service = self.installation.service
        clone_token = service.get_clone_token(self.project)
        assert clone_token == f"x-access-token:{token}"

    @requests_mock.Mocker(kw="request")
    def test_post_comment(self, request):
        version = get(
            Version,
            verbose_name="1234",
            project=self.project,
            type=EXTERNAL,
        )
        build = get(
            Build,
            project=self.project,
            version=version,
        )

        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}/issues/{version.verbose_name}",
            json=self._get_pull_request_json(
                number=int(version.verbose_name),
                repo_full_name=self.remote_repository.full_name,
            ),
        )
        request.get(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/{version.verbose_name}/comments",
            json=[
                self._get_comment_json(
                    id=1,
                    issue_number=int(version.verbose_name),
                    repo_full_name=self.remote_repository.full_name,
                    user={"login": "user"},
                    body="First comment!",
                ),
            ],
        )
        request_post_comment = request.post(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/{version.verbose_name}/comments",
        )

        service = self.installation.service

        # Since there's no existing comment from the bot, it will create a new one.
        service.post_comment(build, "First comment!")

        assert request_post_comment.called
        assert request_post_comment.last_request.json() == {
            "body": f"<!-- readthedocs-{self.project.id} -->\nFirst comment!",
        }

        request.get(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/{version.verbose_name}/comments",
            json=[
                self._get_comment_json(
                    id=1,
                    issue_number=int(version.verbose_name),
                    repo_full_name=self.remote_repository.full_name,
                    user={"login": "user"},
                    body="First comment!",
                ),
                self._get_comment_json(
                    id=2,
                    issue_number=int(version.verbose_name),
                    repo_full_name=self.remote_repository.full_name,
                    user={"login": f"{settings.GITHUB_APP_NAME}[bot]"},
                    body=f"<!-- readthedocs-{self.project.id} -->\nFirst comment!",
                ),
            ],
        )
        request_patch_comment = request.patch(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/comments/2",
            json={},
        )
        request_post_comment.reset()

        # Since there's an existing comment from the bot, it will update it.
        service.post_comment(build, "Second comment!")

        assert not request_post_comment.called
        assert request_patch_comment.called
        assert request_patch_comment.last_request.json() == {
            "body": f"<!-- readthedocs-{self.project.id} -->\nSecond comment!",
        }

        # Another project linked to the same remote repository.
        another_project = get(
            Project,
            users=[self.user],
            remote_repository=self.remote_repository,
        )
        another_version = get(
            Version,
            project=another_project,
            type=EXTERNAL,
            verbose_name="1234",
        )
        another_build = get(
            Build,
            project=another_project,
            version=another_version,
        )

        request_post_comment.reset()

        # There is an existing comment from the bot, but it belongs to another project.
        # So it will create a new comment for the new project.
        service.post_comment(
            another_build,
            "Comment from another project.",
        )

        assert request_post_comment.called
        assert request_post_comment.last_request.json() == {
            "body": f"<!-- readthedocs-{another_project.id} -->\nComment from another project.",
        }

    @requests_mock.Mocker(kw="request")
    def test_post_comment_update_only(self, request):
        version = get(
            Version,
            verbose_name="1234",
            project=self.project,
            type=EXTERNAL,
        )
        build = get(
            Build,
            project=self.project,
            version=version,
        )

        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}/issues/{version.verbose_name}",
            json=self._get_pull_request_json(
                number=int(version.verbose_name),
                repo_full_name=self.remote_repository.full_name,
            ),
        )
        request.get(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/{version.verbose_name}/comments",
            json=[],
        )
        request_post_comment = request.post(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/{version.verbose_name}/comments",
        )

        service = self.installation.service

        # No comments exist, so it will not create a new one.
        service.post_comment(build, "Comment!", create_new=False)
        assert not request_post_comment.called

        request.get(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/{version.verbose_name}/comments",
            json=[
                self._get_comment_json(
                    id=1,
                    issue_number=int(version.verbose_name),
                    repo_full_name=self.remote_repository.full_name,
                    user={"login": f"{settings.GITHUB_APP_NAME}[bot]"},
                    body=f"<!-- readthedocs-{self.project.id} -->\nComment!",
                ),
            ],
        )
        request_patch_comment = request.patch(
            f"{self.api_url}/repos/{self.remote_repository.full_name}/issues/comments/1",
            json={},
        )

        request_post_comment.reset()

        # A comment exists from the bot, so it will update it.
        service.post_comment(build, "Comment!", create_new=False)
        assert not request_post_comment.called

        assert request_patch_comment.called
        assert request_patch_comment.last_request.json() == {
            "body": f"<!-- readthedocs-{self.project.id} -->\nComment!",
        }

    def test_integration_attributes(self):
        assert self.integration.is_active
        assert self.integration.get_absolute_url() == "https://github.com/apps/readthedocs/installations/1111"
        self.project.remote_repository = None
        assert not self.integration.is_active
        assert self.integration.get_absolute_url() is None

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository(self, request):
        assert self.remote_repository.description == "Some description"
        request.post(
            f"{self.api_url}/app/installations/1111/access_tokens",
            json=self._get_access_token_json(),
        )
        request.get(
            f"{self.api_url}/repositories/{self.remote_repository.remote_id}",
            json=self._get_repository_json(
                full_name="user/repo",
                id=int(self.remote_repository.remote_id),
                owner={"id": int(self.account.uid)},
                description="New description",
            ),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/installation",
            json=self._get_installation_json(id=1111),
        )
        request.get(
            f"{self.api_url}/repos/user/repo/collaborators",
            json=[self._get_collaborator_json()],
        )

        service = self.installation.service
        service.update_repository(self.remote_repository)

        self.remote_repository.refresh_from_db()
        assert self.remote_repository.description == "New description"


@override_settings(
    PUBLIC_API_URL="https://app.readthedocs.org",
)
class GitHubOAuthTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username="eric", password="test")
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug="pip")
        self.org = RemoteOrganization.objects.create(
            slug="organization",
            remote_id="1234",
            vcs_provider=GITHUB,
        )
        self.privacy = settings.DEFAULT_PRIVACY_LEVEL
        self.social_github_account = get(
            SocialAccount,
            user=self.user,
            provider=GitHubProvider.id,
        )
        get(
            SocialToken,
            account=self.social_github_account,
        )
        self.service = GitHubService(user=self.user, account=self.social_github_account)
        self.external_version = get(Version, project=self.project, type=EXTERNAL)
        self.external_build = get(
            Build,
            project=self.project,
            version=self.external_version,
            commit="1234",
        )
        self.integration = get(
            GitHubWebhook,
            project=self.project,
            provider_data={"url": "https://github.com/"},
        )
        self.provider_data = [
            {
                "config": {"url": "https://example.com/webhook"},
                "url": "https://api.github.com/repos/test/Hello-World/hooks/12345678",
            }
        ]
        self.repo_response_data = {
            "name": "testrepo",
            "full_name": "testuser/testrepo",
            "id": 12345678,
            "description": "Test Repo",
            "git_url": "git://github.com/testuser/testrepo.git",
            "private": False,
            "ssh_url": "ssh://git@github.com:testuser/testrepo.git",
            "html_url": "https://github.com/testuser/testrepo",
            "clone_url": "https://github.com/testuser/testrepo.git",
            "owner": {
                "type": "User",
                "id": 1234,
            },
            "permissions": {"admin": True, "push": True, "pull": True},
        }
        self.repo_with_org_response_data = copy.deepcopy(self.repo_response_data)
        self.repo_with_org_response_data["owner"] = {
            "login": "organization",
            "id": 1234,
            "node_id": "a1b2c3",
            "url": "https://api.github.com/orgs/organization",
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
        self.api_url = "https://api.github.com"

    def test_create_remote_repository(self):
        repo = self.service.create_repository(
            self.repo_response_data,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, "testrepo")
        self.assertEqual(repo.full_name, "testuser/testrepo")
        self.assertEqual(repo.remote_id, "12345678")
        self.assertEqual(repo.vcs_provider, GITHUB)
        self.assertEqual(repo.description, "Test Repo")
        self.assertEqual(
            repo.avatar_url,
            settings.OAUTH_AVATAR_USER_DEFAULT_URL,
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, None)
        self.assertEqual(
            repo.clone_url,
            "https://github.com/testuser/testrepo.git",
        )
        self.assertEqual(
            repo.ssh_url,
            "ssh://git@github.com:testuser/testrepo.git",
        )
        self.assertEqual(repo.html_url, "https://github.com/testuser/testrepo")

    def test_create_remote_repository_with_organization(self):
        repo = self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, "testrepo")
        self.assertEqual(repo.full_name, "testuser/testrepo")
        self.assertEqual(repo.remote_id, "12345678")
        self.assertEqual(repo.vcs_provider, GITHUB)
        self.assertEqual(repo.description, "Test Repo")
        self.assertEqual(
            repo.avatar_url,
            settings.OAUTH_AVATAR_USER_DEFAULT_URL,
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url,
            "https://github.com/testuser/testrepo.git",
        )
        self.assertEqual(
            repo.ssh_url,
            "ssh://git@github.com:testuser/testrepo.git",
        )
        self.assertEqual(repo.html_url, "https://github.com/testuser/testrepo")

    def test_create_remote_repository_with_new_organization(self):
        self.org.delete()
        repo = self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, "testrepo")
        self.assertEqual(repo.full_name, "testuser/testrepo")
        self.assertEqual(repo.remote_id, "12345678")
        self.assertEqual(repo.vcs_provider, GITHUB)
        self.assertEqual(repo.description, "Test Repo")
        self.assertEqual(
            repo.avatar_url,
            settings.OAUTH_AVATAR_USER_DEFAULT_URL,
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(
            repo.clone_url,
            "https://github.com/testuser/testrepo.git",
        )
        self.assertEqual(
            repo.ssh_url,
            "ssh://git@github.com:testuser/testrepo.git",
        )
        self.assertEqual(repo.html_url, "https://github.com/testuser/testrepo")
        org = repo.organization

        self.assertEqual(org.remote_id, "1234")
        self.assertEqual(org.slug, "organization")
        self.assertEqual(org.url, "https://github.com/organization")

    def test_skip_creation_remote_repository_on_private_repos(self):
        self.repo_response_data["private"] = True
        github_project = self.service.create_repository(
            self.repo_response_data,
            privacy=self.privacy,
        )
        self.assertIsNone(github_project)

    def test_project_was_moved_from_a_personal_account_to_an_organization(self):
        github_project = self.service.create_repository(
            self.repo_response_data,
            privacy=self.privacy,
        )
        self.assertEqual(github_project.organization, None)

        # Project has been moved to an organization.
        self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        github_project.refresh_from_db()
        self.assertEqual(github_project.organization, self.org)

    def test_project_was_moved_from_an_organization_to_a_personal_account(self):
        # Project belongs to an organization.
        github_project = self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        self.assertEqual(github_project.organization, self.org)

        # Project has been moved to a personal account.
        self.service.create_repository(
            self.repo_response_data,
            privacy=self.privacy,
        )
        github_project.refresh_from_db()
        self.assertEqual(github_project.organization, None)

    def test_project_was_moved_to_another_organization(self):
        another_remote_organization = RemoteOrganization.objects.create(
            slug="another",
            remote_id="4321",
            vcs_provider=GITHUB,
        )

        # Project belongs to an organization.
        github_project = self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        self.assertEqual(github_project.organization, self.org)

        # Project was moved to another organization.
        self.repo_with_org_response_data["owner"]["id"] = 4321
        self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        github_project.refresh_from_db()
        self.assertEqual(github_project.organization, another_remote_organization)

    def test_make_organization(self):
        org_json = {
            "id": 12345,
            "html_url": "https://github.com/testorg",
            "name": "Test Org",
            "email": "test@testorg.org",
            "login": "testorg",
            "avatar_url": "https://images.github.com/foobar",
        }
        org = self.service.create_organization(org_json)
        self.assertIsInstance(org, RemoteOrganization)
        self.assertEqual(org.slug, "testorg")
        self.assertEqual(org.name, "Test Org")
        self.assertEqual(org.email, "test@testorg.org")
        self.assertEqual(org.avatar_url, "https://images.github.com/foobar")
        self.assertEqual(org.url, "https://github.com/testorg")

    def test_import_with_no_token(self):
        """User without a GitHub SocialToken does not return a service."""
        services = list(GitHubService.for_user(get(User)))
        self.assertEqual(services, [])

    def test_multiple_users_same_repo(self):
        github_project = self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )

        user2 = User.objects.get(pk=2)
        service = GitHubService(user=user2, account=get(SocialAccount, user=self.user))
        github_project_2 = service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        self.assertIsInstance(github_project, RemoteRepository)
        self.assertIsInstance(github_project_2, RemoteRepository)
        self.assertEqual(github_project_2, github_project)

        github_project_3 = self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        github_project_4 = service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        self.assertIsInstance(github_project_3, RemoteRepository)
        self.assertIsInstance(github_project_4, RemoteRepository)
        self.assertEqual(github_project, github_project_3)
        self.assertEqual(github_project_2, github_project_4)

        github_project_5 = self.service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )
        github_project_6 = service.create_repository(
            self.repo_with_org_response_data,
            privacy=self.privacy,
        )

        self.assertIsNotNone(github_project)
        self.assertEqual(github_project, github_project_5)
        self.assertIsNotNone(github_project_2)
        self.assertEqual(github_project_2, github_project_6)

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_send_build_status_successful(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 201
        success = self.service.send_build_status(
            build=self.external_build,
            commit=self.external_build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        self.assertTrue(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(http_status_code=201)
        mock_logger.debug.assert_called_with(
            "GitHub commit status created for project.",
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_send_build_status_on_pr_builds(self, session, mock_logger, mock_structlog):
        """Test that when status is SUCCESS but version is not built, it links to build detail page.

        This happens when a build has exit code 183 (skipped) - it reports SUCCESS
        to GitHub so the PR can be merged, but the version is never marked as built.
        """
        # external_version.built is False by default
        session.post.return_value.status_code = 201
        success = self.service.send_build_status(
            build=self.external_build,
            commit=self.external_build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        self.assertTrue(success)
        # Verify that the target_url points to the build detail page, not the version docs
        call_args = mock_structlog.contextvars.bind_contextvars.call_args_list
        # Find the call with target_url
        target_url = None
        for call in call_args:
            if 'target_url' in call[1]:
                target_url = call[1]['target_url']
                break

        self.assertIsNotNone(target_url)
        # Should link to build detail page, not version URL
        self.assertIn(f'/projects/{self.project.slug}/builds/{self.external_build.pk}/', target_url)
        self.assertNotIn('.readthedocs.io', target_url)

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_send_build_status_404_error(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 404
        success = self.service.send_build_status(
            build=self.external_build,
            commit=self.external_build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        self.assertFalse(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(http_status_code=404)
        mock_logger.info.assert_called_with(
            "GitHub project does not exist or user does not have permissions.",
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_send_build_status_value_error(self, session, mock_logger, mock_structlog):
        session.post.side_effect = ValueError
        success = self.service.send_build_status(
            build=self.external_build,
            commit=self.external_build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        self.assertFalse(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            commit_status="success",
            user_username=self.user.username,
            statuses_url="https://api.github.com/repos/pypa/pip/statuses/1234",
            target_url=mock.ANY,
            status="success",
        )
        mock_logger.exception.assert_called_with(
            "GitHub commit status creation failed for project.",
        )

    @override_settings(DEFAULT_PRIVACY_LEVEL="private")
    def test_create_public_repo_when_private_projects_are_enabled(self):
        """Test ability to import ``public`` repositories under ``private`` level."""
        repo = self.service.create_repository(self.repo_with_org_response_data)
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(repo.remote_id, str(self.repo_with_org_response_data["id"]))


    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_setup_webhook_successful(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 201
        session.post.return_value.json.return_value = {}
        success = self.service.setup_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(http_status_code=201)
        mock_logger.debug.assert_called_with(
            "GitHub webhook creation successful for project.",
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_setup_webhook_404_error(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 404
        success = self.service.setup_webhook(self.project, self.integration)
        self.integration.refresh_from_db()

        self.assertFalse(success)
        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(http_status_code=404)
        mock_logger.warning.assert_called_with(
            "GitHub project does not exist or user does not have permissions.",
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_setup_webhook_value_error(self, session, mock_logger, mock_structlog):
        session.post.side_effect = ValueError
        self.service.setup_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.github.com/repos/pypa/pip/hooks",
        )
        mock_logger.exception.assert_called_with(
            "GitHub webhook creation failed for project.",
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_update_webhook_successful(self, session, mock_logger, mock_structlog):
        session.patch.return_value.status_code = 201
        session.patch.return_value.json.return_value = {}
        success = self.service.update_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            http_status_code=201,
            url="https://github.com/",
        )
        mock_logger.info.assert_called_with(
            "GitHub webhook update successful for project.",
        )

    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.setup_webhook")
    def test_update_webhook_404_error(self, setup_webhook, session):
        session.patch.return_value.status_code = 404
        self.service.update_webhook(self.project, self.integration)

        setup_webhook.assert_called_once_with(self.project, self.integration)

    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.setup_webhook")
    def test_update_webhook_no_provider_data(self, setup_webhook, session):
        self.integration.provider_data = {}
        self.integration.save()

        session.patch.side_effect = AttributeError
        self.service.update_webhook(self.project, self.integration)

        setup_webhook.assert_called_once_with(self.project, self.integration)

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_update_webhook_value_error(self, session, mock_logger, mock_structlog):
        session.patch.side_effect = ValueError
        self.service.update_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertIsNotNone(self.integration.secret)
        mock_logger.exception.assert_called_with(
            "GitHub webhook update failed for project."
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_get_provider_data_successful(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        webhook_data = self.provider_data
        rtd_webhook_url = "{domain}{path}".format(
            domain=settings.PUBLIC_API_URL,
            path=reverse(
                "api_webhook",
                kwargs={
                    "project_slug": self.project.slug,
                    "integration_pk": self.integration.pk,
                },
            ),
        )
        webhook_data[0]["config"]["url"] = rtd_webhook_url

        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = webhook_data

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, webhook_data[0])
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.github.com/repos/pypa/pip/hooks",
        )
        mock_logger.info.assert_called_with(
            "GitHub integration updated with provider data for project.",
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_get_provider_data_404_error(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        session.get.return_value.status_code = 404

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_logger.warning.assert_called_with(
            "GitHub project does not exist or user does not have permissions.",
            https_status_code=404,
        )

    @mock.patch("readthedocs.oauth.services.github.structlog")
    @mock.patch("readthedocs.oauth.services.github.log")
    @mock.patch("readthedocs.oauth.services.github.GitHubService.session")
    def test_get_provider_data_attribute_error(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        session.get.side_effect = AttributeError

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.github.com/repos/pypa/pip/hooks",
        )
        mock_logger.exception.assert_called_with(
            "GitHub webhook Listing failed for project.",
        )

    @requests_mock.Mocker(kw="request")
    def test_remove_webhook_match_found(self, request):
        assert self.project.repo == "https://github.com/pypa/pip"
        assert self.project.slug == "pip"
        request.get(
            f"{self.api_url}/repos/pypa/pip/hooks",
            json=[
                {
                    "id": 1,
                    "config": {
                        "url": "https://readthedocs.org/api/v2/webhook/github/pip/1111/",
                    },
                },
                {
                    "id": 2,
                    "config": {
                        "url": "https://readthedocs.org/api/v2/webhook/pip/1111/",
                    },
                },
                {
                    "id": 3,
                    "config": {
                        "url": "https://app.readthedocs.org/api/v2/webhook/github/pip/1111/",
                    },
                },
                {
                    "id": 4,
                    "config": {
                        "url": "https://app.readthedocs.org/api/v2/webhook/pip/1111/",
                    },
                },
                {
                    "id": 5,
                    "config": {
                        "url": "https://readthedocs.org/api/v2/webhook/github/another-project/1111/",
                    },
                },
                {
                    "id": 6,
                    "config": {
                        "url": "https://example.com/dont-delete-me/",
                    },
                },
            ],
        )
        mock_request_deletions = [
            request.delete(
                f"{self.api_url}/repos/pypa/pip/hooks/1",
            ),
            request.delete(
                f"{self.api_url}/repos/pypa/pip/hooks/2",
            ),
            request.delete(
                f"{self.api_url}/repos/pypa/pip/hooks/3",
            ),
            request.delete(
                f"{self.api_url}/repos/pypa/pip/hooks/4",
            ),
        ]
        assert self.service.remove_webhook(self.project) is True
        for mock_request_deletion in mock_request_deletions:
            assert mock_request_deletion.called_once

    @requests_mock.Mocker(kw="request")
    def test_remove_webhook_match_found_error_to_delete(self, request):
        assert self.project.repo == "https://github.com/pypa/pip"
        assert self.project.slug == "pip"
        request.get(
            f"{self.api_url}/repos/pypa/pip/hooks",
            json=[
                {
                    "id": 1,
                    "config": {
                        "url": "https://readthedocs.org/api/v2/webhook/github/pip/1111/",
                    },
                },
                {
                    "id": 2,
                    "config": {
                        "url": "https://readthedocs.org/api/v2/webhook/pip/1111/",
                    },
                },
                {
                    "id": 3,
                    "config": {
                        "url": "https://app.readthedocs.org/api/v2/webhook/github/pip/1111/",
                    },
                },
                {
                    "id": 4,
                    "config": {
                        "url": "https://app.readthedocs.org/api/v2/webhook/pip/1111/",
                    },
                },
                {
                    "id": 5,
                    "config": {
                        "url": "https://readthedocs.org/api/v2/webhook/github/another-project/1111/",
                    },
                },
                {
                    "id": 6,
                    "config": {
                        "url": "https://example.com/dont-delete-me/",
                    },
                },
            ],
        )
        mock_request_deletion = request.delete(
            f"{self.api_url}/repos/pypa/pip/hooks/1",
            status_code=401,
        )
        assert self.service.remove_webhook(self.project) is False
        assert mock_request_deletion.called_once

    @requests_mock.Mocker(kw="request")
    def test_remove_webhook_match_not_found(self, request):
        assert self.project.repo == "https://github.com/pypa/pip"
        assert self.project.slug == "pip"
        request.get(
            f"{self.api_url}/repos/pypa/pip/hooks",
            json=[
                {
                    "id": 1,
                    "config": {
                        "url": "https://readthedocs.org/api/v2/webhook/github/another-project/1111/",
                    },
                },
                {
                    "id": 2,
                    "config": {
                        "url": "https://example.com/dont-delete-me/",
                    },
                },
            ],
        )
        assert self.service.remove_webhook(self.project) is True

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=GITHUB,
            full_name="testuser/testrepo",
            remote_id=self.repo_response_data["id"],
        )
        assert not remote_repo.users.filter(id=self.user.id).exists()

        request.get(f"https://api.github.com/repositories/{remote_repo.remote_id}", json=self.repo_response_data)
        self.service.update_repository(remote_repo)
        remote_repo.refresh_from_db()

        assert remote_repo.name == "testrepo"
        assert remote_repo.full_name == "testuser/testrepo"
        assert remote_repo.description == "Test Repo"
        assert remote_repo.users.filter(id=self.user.id).exists()
        relation = remote_repo.remote_repository_relations.get(user=self.user)
        assert relation.account == self.social_github_account
        assert relation.admin

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository_remove_user_relation(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=GITHUB,
            full_name="testuser/testrepo",
            remote_id=self.repo_response_data["id"],
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_github_account,
            remote_repository=remote_repo,
            admin=True,
        )
        assert remote_repo.users.filter(id=self.user.id).exists()

        request.get(f"https://api.github.com/repositories/{remote_repo.remote_id}", status_code=404)
        self.service.update_repository(remote_repo)
        remote_repo.refresh_from_db()

        assert remote_repo.full_name == "testuser/testrepo"
        assert not remote_repo.description
        assert not remote_repo.users.filter(id=self.user.id).exists()

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository_remove_user_relation_public_repo(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=GITHUB,
            full_name="testuser/testrepo",
            remote_id=self.repo_response_data["id"],
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_github_account,
            remote_repository=remote_repo,
            admin=True,
        )
        assert remote_repo.users.filter(id=self.user.id).exists()

        for k in self.repo_response_data["permissions"]:
            self.repo_response_data["permissions"][k] = False

        request.get(f"https://api.github.com/repositories/{remote_repo.remote_id}", json=self.repo_response_data)
        self.service.update_repository(remote_repo)
        remote_repo.refresh_from_db()

        assert remote_repo.name == "testrepo"
        assert remote_repo.full_name == "testuser/testrepo"
        assert remote_repo.description == "Test Repo"
        assert not remote_repo.users.filter(id=self.user.id).exists()


class BitbucketOAuthTests(TestCase):
    fixtures = ["eric", "test_data"]

    def setUp(self):
        self.client.login(username="eric", password="test")
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug="pip")
        self.project.repo = "https://bitbucket.org/testuser/testrepo/"
        self.project.save()
        self.org = RemoteOrganization.objects.create(
            remote_id="{61fc5cf6-d054-47d2-b4a9-061ccf858379}",
            slug="teamsinspace",
            vcs_provider=BITBUCKET,
        )
        self.privacy = settings.DEFAULT_PRIVACY_LEVEL
        self.social_account = get(
            SocialAccount,
            user=self.user,
            provider=BitbucketOAuth2Provider.id,
        )
        get(
            SocialToken,
            account=self.social_account,
        )
        self.service = BitbucketService(
            user=self.user, account=self.social_account,
        )
        self.integration = get(
            GitHubWebhook,
            project=self.project,
            provider_data={"links": {"self": {"href": "https://bitbucket.org/"}}},
        )
        self.provider_data = {
            "values": [
                {
                    "links": {"self": {"href": "https://bitbucket.org/"}},
                    "url": "https://readthedocs.io/api/v2/webhook/test/99999999/",
                },
            ]
        }
        self.team_response_data = {
            "slug": self.org.slug,
            "name": "Teams In Space",
            "uuid": self.org.remote_id,
            "links": {
                "self": {
                    "href": "https://api.bitbucket.org/2.0/workspaces/teamsinspace",
                },
                "repositories": {
                    "href": "https://api.bitbucket.org/2.0/repositories/teamsinspace",
                },
                "html": {"href": "https://bitbucket.org/teamsinspace"},
                "avatar": {
                    "href": "https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2014/Sep/24/teamsinspace-avatar-3731530358-7_avatar.png",
                },
                "members": {
                    "href": "https://api.bitbucket.org/2.0/workspaces/teamsinspace/members",
                },
                "owners": {
                    "href": "https://api.bitbucket.org/2.0/workspaces/teamsinspace/members?q=permission%3D%22owner%22",
                },
                "hooks": {
                    "href": "https://api.bitbucket.org/2.0/workspaces/teamsinspace/hooks",
                },
                "snippets": {
                    "href": "https://api.bitbucket.org/2.0/snippets/teamsinspace/",
                },
                "projects": {
                    "href": "https://api.bitbucket.org/2.0/workspaces/teamsinspace/projects",
                },
            },
            "created_on": "2014-04-08T00:00:14.070969+00:00",
            "type": "workspace",
            "is_private": True,
        }
        self.repo_response_data = {
            "scm": "hg",
            "has_wiki": True,
            "description": "Site for tutorial101 files",
            "links": {
                "watchers": {
                    "href": "https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/watchers",
                },
                "commits": {
                    "href": "https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/commits",
                },
                "self": {
                    "href": "https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org",
                },
                "html": {
                    "href": "https://bitbucket.org/tutorials/tutorials.bitbucket.org",
                },
                "avatar": {
                    "href": "https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2012/Nov/28/tutorials.bitbucket.org-logo-1456883302-9_avatar.png",
                },
                "forks": {
                    "href": "https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/forks",
                },
                "clone": [
                    {
                        "href": "https://tutorials@bitbucket.org/tutorials/tutorials.bitbucket.org",
                        "name": "https",
                    },
                    {
                        "href": "ssh://hg@bitbucket.org/tutorials/tutorials.bitbucket.org",
                        "name": "ssh",
                    },
                ],
                "pullrequests": {
                    "href": "https://api.bitbucket.org/2.0/repositories/tutorials/tutorials.bitbucket.org/pullrequests",
                },
            },
            "fork_policy": "allow_forks",
            "name": "tutorials.bitbucket.org",
            "language": "html/css",
            "created_on": "2011-12-20T16:35:06.480042+00:00",
            "full_name": "tutorials/tutorials.bitbucket.org",
            "has_issues": True,
            "workspace": self.team_response_data,
            "owner": {
                "username": "tutorials",
                "display_name": "tutorials account",
                "uuid": "{c788b2da-b7a2-404c-9e26-d3f077557007}",
                "links": {
                    "self": {
                        "href": "https://api.bitbucket.org/2.0/users/tutorials",
                    },
                    "html": {
                        "href": "https://bitbucket.org/tutorials",
                    },
                    "avatar": {
                        "href": "https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2013/Nov/25/tutorials-avatar-1563784409-6_avatar.png",
                    },
                },
            },
            "updated_on": "2014-11-03T02:24:08.409995+00:00",
            "size": 76182262,
            "is_private": False,
            "uuid": "{9970a9b6-2d86-413f-8555-da8e1ac0e542}",
            "mainbranch": {
                "type": "branch",
                "name": "main",
            },
        }

    def test_make_project_pass(self):
        repo = self.service.create_repository(
            self.repo_response_data,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, "tutorials.bitbucket.org")
        self.assertEqual(repo.full_name, "tutorials/tutorials.bitbucket.org")
        self.assertEqual(repo.remote_id, "{9970a9b6-2d86-413f-8555-da8e1ac0e542}")
        self.assertEqual(repo.vcs_provider, BITBUCKET)
        self.assertEqual(repo.description, "Site for tutorial101 files")
        self.assertEqual(repo.default_branch, "main")
        self.assertEqual(
            repo.avatar_url,
            (
                "https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2012/Nov/28/"
                "tutorials.bitbucket.org-logo-1456883302-9_avatar.png"
            ),
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url,
            "https://bitbucket.org/tutorials/tutorials.bitbucket.org",
        )
        self.assertEqual(
            repo.ssh_url,
            "ssh://hg@bitbucket.org/tutorials/tutorials.bitbucket.org",
        )
        self.assertEqual(
            repo.html_url,
            "https://bitbucket.org/tutorials/tutorials.bitbucket.org",
        )

    def test_make_project_mainbranch_none(self):
        self.repo_response_data["mainbranch"] = None
        repo = self.service.create_repository(
            self.repo_response_data,
            privacy=self.privacy,
        )
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, "tutorials.bitbucket.org")
        self.assertEqual(repo.full_name, "tutorials/tutorials.bitbucket.org")
        self.assertEqual(repo.description, "Site for tutorial101 files")
        self.assertEqual(
            repo.avatar_url,
            (
                "https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2012/Nov/28/"
                "tutorials.bitbucket.org-logo-1456883302-9_avatar.png"
            ),
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url,
            "https://bitbucket.org/tutorials/tutorials.bitbucket.org",
        )
        self.assertEqual(
            repo.ssh_url,
            "ssh://hg@bitbucket.org/tutorials/tutorials.bitbucket.org",
        )
        self.assertEqual(
            repo.html_url,
            "https://bitbucket.org/tutorials/tutorials.bitbucket.org",
        )
        self.assertEqual(repo.default_branch, None)

    def test_make_project_fail(self):
        data = self.repo_response_data.copy()
        data["is_private"] = True
        repo = self.service.create_repository(
            data,
            privacy=self.privacy,
        )
        self.assertIsNone(repo)

    @override_settings(DEFAULT_PRIVACY_LEVEL="private")
    def test_make_private_project(self):
        """
        Test ability to import ``public`` repositories under ``private`` level.
        """
        data = self.repo_response_data.copy()
        data["is_private"] = False
        repo = self.service.create_repository(data)
        self.assertIsNotNone(repo)

    def test_make_organization(self):
        org = self.service.create_organization(self.team_response_data)
        self.assertIsInstance(org, RemoteOrganization)
        self.assertEqual(org.slug, "teamsinspace")
        self.assertEqual(org.name, "Teams In Space")
        self.assertEqual(
            org.avatar_url,
            (
                "https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2014/Sep/24/"
                "teamsinspace-avatar-3731530358-7_avatar.png"
            ),
        )
        self.assertEqual(org.url, "https://bitbucket.org/teamsinspace")

    def test_import_with_no_token(self):
        """User without a Bitbucket SocialToken does not return a service."""
        services = list(BitbucketService.for_user(get(User)))
        self.assertEqual(services, [])

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_setup_webhook_successful(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 201
        session.post.return_value.json.return_value = {}
        success = self.service.setup_webhook(self.project, self.integration)

        self.assertTrue(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks",
        )
        mock_logger.debug.assert_called_with(
            "Bitbucket webhook creation successful for project.",
        )

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_setup_webhook_404_error(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 404
        success = self.service.setup_webhook(self.project, self.integration)

        self.assertFalse(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks",
        )
        mock_logger.info.assert_called_with(
            "Bitbucket project does not exist or user does not have permissions.",
        )

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_setup_webhook_value_error(self, session, mock_logger, mock_structlog):
        session.post.side_effect = ValueError
        self.service.setup_webhook(self.project, self.integration)

        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks",
        )
        mock_logger.exception.assert_called_with(
            "Bitbucket webhook creation failed for project.",
        )

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_update_webhook_successful(self, session, mock_logger, mock_structlog):
        session.put.return_value.status_code = 200
        session.put.return_value.json.return_value = {}
        success = self.service.update_webhook(self.project, self.integration)

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(project_slug=self.project.slug)
        mock_logger.info.assert_called_with(
            "Bitbucket webhook update successful for project.",
        )

    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.setup_webhook")
    def test_update_webhook_404_error(self, setup_webhook, session):
        session.put.return_value.status_code = 404
        self.service.update_webhook(self.project, self.integration)

        setup_webhook.assert_called_once_with(self.project, self.integration)

    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.setup_webhook")
    def test_update_webhook_no_provider_data(self, setup_webhook, session):
        self.integration.provider_data = {}
        self.integration.save()

        session.put.side_effect = AttributeError
        self.service.update_webhook(self.project, self.integration)

        setup_webhook.assert_called_once_with(self.project, self.integration)

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_update_webhook_value_error(self, session, mock_logger, mock_structlog):
        session.put.side_effect = ValueError
        self.service.update_webhook(self.project, self.integration)

        mock_structlog.contextvars.bind_contextvars.assert_called_with(project_slug=self.project.slug)
        mock_logger.exception.assert_called_with(
            "Bitbucket webhook update failed for project.",
        )

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_get_provider_data_successful(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        webhook_data = self.provider_data
        rtd_webhook_url = "https://{domain}{path}".format(
            domain=settings.PRODUCTION_DOMAIN,
            path=reverse(
                "api_webhook",
                kwargs={
                    "project_slug": self.project.slug,
                    "integration_pk": self.integration.pk,
                },
            ),
        )
        webhook_data["values"][0]["url"] = rtd_webhook_url

        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = webhook_data

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, webhook_data["values"][0])
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks",
        )
        mock_logger.info.assert_called_with(
            "Bitbucket integration updated with provider data for project.",
        )

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_get_provider_data_404_error(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        session.get.return_value.status_code = 404

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks",
        )
        mock_logger.info.assert_called_with(
            "Bitbucket project does not exist or user does not have permissions.",
        )

    @mock.patch("readthedocs.oauth.services.bitbucket.structlog")
    @mock.patch("readthedocs.oauth.services.bitbucket.log")
    @mock.patch("readthedocs.oauth.services.bitbucket.BitbucketService.session")
    def test_get_provider_data_attribute_error(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        session.get.side_effect = AttributeError

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://api.bitbucket.org/2.0/repositories/testuser/testrepo/hooks",
        )
        mock_logger.exception.assert_called_with(
            "Bitbucket webhook Listing failed for project.",
        )

    def test_project_moved_between_groups(self):
        repo = self.service.create_repository(self.repo_response_data)
        assert repo.organization == self.org
        assert repo.name == "tutorials.bitbucket.org"
        assert repo.full_name == "tutorials/tutorials.bitbucket.org"
        assert not repo.private
        assert repo.remote_repository_relations.count() == 1
        relationship = repo.remote_repository_relations.first()
        assert not relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

        self.repo_response_data["workspace"] = {
            "kind": "workspace",
            "slug": "testorg",
            "name": "Test Org",
            "uuid": "6",
            "links": {
                "html": {"href": "https://bitbucket.org/testorg"},
                "avatar": {
                    "href": "https://bitbucket-assetroot.s3.amazonaws.com/c/photos/2014/Sep/24/teamsinspace-avatar-3731530358-7_avatar.png",
                },
            },
        }

        repo_b = self.service.create_repository(self.repo_response_data)
        assert repo_b == repo
        repo.refresh_from_db()
        another_group = RemoteOrganization.objects.get(
            remote_id="6",
            vcs_provider=BITBUCKET,
        )
        assert repo.organization == another_group
        relationship = repo.remote_repository_relations.first()
        assert not relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=BITBUCKET,
            full_name="testuser/testrepo",
            remote_id=self.repo_response_data["uuid"],
        )
        assert not remote_repo.users.filter(id=self.user.id).exists()

        request.get(f"https://api.bitbucket.org/2.0/repositories/?role=admin", json={"values": [self.repo_response_data]})
        request.get(f"https://api.bitbucket.org/2.0/repositories/?role=member", json={"values": [self.repo_response_data]})
        self.service.update_repository(remote_repo)
        remote_repo.refresh_from_db()

        assert remote_repo.name == "tutorials.bitbucket.org"
        assert remote_repo.full_name == "tutorials/tutorials.bitbucket.org"
        assert remote_repo.description == "Site for tutorial101 files"
        assert remote_repo.users.filter(id=self.user.id).exists()
        relation = remote_repo.remote_repository_relations.get(user=self.user)
        assert relation.account == self.social_account
        assert relation.admin

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository_remove_user_relation(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=BITBUCKET,
            full_name="testuser/testrepo",
            remote_id=self.repo_response_data["uuid"],
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_account,
            remote_repository=remote_repo,
            admin=True,
        )
        assert remote_repo.users.filter(id=self.user.id).exists()

        request.get(f"https://api.bitbucket.org/2.0/repositories/?role=admin", json={"values": []})
        request.get(f"https://api.bitbucket.org/2.0/repositories/?role=member", json={"values": []})
        self.service.update_repository(remote_repo)
        remote_repo.refresh_from_db()

        assert remote_repo.full_name == "testuser/testrepo"
        assert not remote_repo.description
        assert not remote_repo.users.filter(id=self.user.id).exists()


class GitLabOAuthTests(TestCase):
    fixtures = ["eric", "test_data"]

    repo_response_data = {
        "lfs_enabled": True,
        "request_access_enabled": False,
        "approvals_before_merge": 0,
        "forks_count": 12,
        "only_allow_merge_if_all_discussions_are_resolved": False,
        "container_registry_enabled": True,
        "web_url": "https://gitlab.com/testorga/testrepo",
        "owner": {
            "username": "testorga",
            "web_url": "https://gitlab.com/testorga",
            "name": "Test Orga",
            "state": "active",
            "avatar_url": "https://secure.gravatar.com/avatar/test",
            "id": 42,
        },
        "wiki_enabled": True,
        "id": 42,
        "merge_requests_enabled": True,
        "archived": False,
        "snippets_enabled": True,
        "http_url_to_repo": "https://gitlab.com/testorga/testrepo.git",
        "namespace": {
            "kind": "user",
            "name": "Test Orga",
            "parent_id": None,
            "plan": "early_adopter",
            "path": "testorga",
            "id": 42,
            "full_path": "testorga",
        },
        "star_count": 1,
        "_links": {
            "repo_branches": "http://gitlab.com/api/v4/projects/42/repository/branches",
            "merge_requests": "http://gitlab.com/api/v4/projects/42/merge_requests",
            "self": "http://gitlab.com/api/v4/projects/42",
            "labels": "http://gitlab.com/api/v4/projects/42/labels",
            "members": "http://gitlab.com/api/v4/projects/42/members",
            "events": "http://gitlab.com/api/v4/projects/42/events",
            "issues": "http://gitlab.com/api/v4/projects/42/issues",
        },
        "resolve_outdated_diff_discussions": False,
        "issues_enabled": True,
        "path_with_namespace": "testorga/testrepo",
        "ci_config_path": None,
        "shared_with_groups": [],
        "description": "Test Repo",
        "default_branch": "master",
        "visibility": "public",
        "ssh_url_to_repo": "git@gitlab.com:testorga/testrepo.git",
        "public_jobs": True,
        "path": "testrepo",
        "import_status": "none",
        "only_allow_merge_if_pipeline_succeeds": False,
        "open_issues_count": 0,
        "last_activity_at": "2017-11-28T14:21:17.570Z",
        "name": "testrepo",
        "printing_merge_request_link_enabled": True,
        "name_with_namespace": "testorga / testrepo",
        "created_at": "2017-11-27T19:19:30.906Z",
        "shared_runners_enabled": True,
        "creator_id": 389803,
        "avatar_url": None,
        "permissions": {
            "group_access": None,
            "project_access": {
                "notification_level": 3,
                "access_level": 40,
            },
        },
        "tag_list": [],
        "jobs_enabled": True,
    }

    group_response_data = {
        "id": 1,
        "name": "Test Orga",
        "path": "testorga",
        "description": "An interesting group",
        "visibility": "public",
        "lfs_enabled": True,
        "avatar_url": "https://secure.gravatar.com/avatar/test",
        "web_url": "https://gitlab.com/groups/testorga",
        "request_access_enabled": False,
        "full_name": "Test Orga",
        "full_path": "group/testorga",
        "parent_id": None,
    }

    def setUp(self):
        self.client.login(username="eric", password="test")
        self.user = User.objects.get(pk=1)
        self.project = Project.objects.get(slug="pip")
        self.project.repo = "https://gitlab.com/testorga/testrepo"
        self.project.save()
        self.org = RemoteOrganization.objects.create(
            remote_id="1",
            slug="testorga",
            vcs_provider=GITLAB,
        )
        self.privacy = settings.DEFAULT_PRIVACY_LEVEL
        self.social_account = get(
            SocialAccount,
            user=self.user,
            provider=GitLabProvider.id,
        )
        get(
            SocialToken,
            account=self.social_account,
        )
        self.service = GitLabService(
            user=self.user, account=self.social_account
        )
        self.external_version = get(Version, project=self.project, type=EXTERNAL)
        self.external_build = get(
            Build,
            project=self.project,
            version=self.external_version,
            commit=1234,
        )
        self.integration = get(
            GitLabWebhook, project=self.project, provider_data={"id": "999999999"}
        )
        self.provider_data = [
            {
                "id": 1084320,
                "url": "https://readthedocs.io/api/v2/webhook/test/99999999/",
            }
        ]

    def get_private_repo_data(self):
        """Manipulate repo response data to get private repo data."""
        data = self.repo_response_data.copy()
        data.update(
            {
                "visibility": "private",
            }
        )
        return data

    def test_project_path_is_escaped(self):
        repo_id = self.service._get_repo_id(self.project)
        self.assertEqual(repo_id, "testorga%2Ftestrepo")

        self.project.repo = "https://gitlab.com/testorga/subgroup/testrepo.git"
        self.project.save()
        repo_id = self.service._get_repo_id(self.project)
        self.assertEqual(repo_id, "testorga%2Fsubgroup%2Ftestrepo")

    def test_make_project_pass(self):
        self.repo_response_data["namespace"] = {
            "kind": "group",
            "name": "Test Orga",
            "path": "testorga",
            "id": self.org.remote_id,
            "full_path": self.org.slug,
        }
        repo = self.service.create_repository(self.repo_response_data, privacy=self.privacy)
        self.assertIsInstance(repo, RemoteRepository)
        self.assertEqual(repo.name, "testrepo")
        self.assertEqual(repo.full_name, "testorga/testrepo")
        self.assertEqual(repo.remote_id, 42)
        self.assertEqual(repo.vcs_provider, GITLAB)
        self.assertEqual(repo.description, "Test Repo")
        self.assertEqual(
            repo.avatar_url,
            "https://secure.gravatar.com/avatar/test",
        )
        self.assertIn(self.user, repo.users.all())
        self.assertEqual(repo.organization, self.org)
        self.assertEqual(
            repo.clone_url,
            "https://gitlab.com/testorga/testrepo.git",
        )
        self.assertEqual(repo.ssh_url, "git@gitlab.com:testorga/testrepo.git")
        self.assertEqual(repo.html_url, "https://gitlab.com/testorga/testrepo")
        self.assertTrue(repo.remote_repository_relations.first().admin)
        self.assertFalse(repo.private)

    def test_make_private_project_fail(self):
        data = self.get_private_repo_data()
        repo = self.service.create_repository(data, privacy=self.privacy)
        self.assertIsNone(repo)

    def test_make_private_project_success(self):
        data = self.get_private_repo_data()
        data["namespace"] = {
            "kind": "group",
            "name": "Test Orga",
            "path": "testorga",
            "id": self.org.remote_id,
            "full_path": self.org.slug,
        }
        repo = self.service.create_repository(data, privacy=constants.PRIVATE)
        self.assertIsInstance(repo, RemoteRepository)
        self.assertTrue(repo.private, True)

    def test_make_organization(self):
        org = self.service.create_organization(self.group_response_data)
        self.assertIsInstance(org, RemoteOrganization)
        self.assertEqual(org.slug, "group/testorga")
        self.assertEqual(org.name, "Test Orga")
        self.assertEqual(
            org.avatar_url,
            "https://secure.gravatar.com/avatar/test",
        )
        self.assertEqual(org.url, "https://gitlab.com/groups/testorga")

    @override_settings(DEFAULT_PRIVACY_LEVEL="private")
    def test_make_private_project(self):
        """
        Test ability to import ``public`` repositories under ``private`` level.
        """
        data = self.repo_response_data.copy()
        data["visibility"] = "public"
        repo = self.service.create_repository(data)
        self.assertIsNotNone(repo)

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService._get_repo_id")
    def test_send_build_status_successful(self, repo_id, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 201
        repo_id().return_value = "9999"

        success = self.service.send_build_status(
            build=self.external_build,
            commit=self.external_build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        self.assertTrue(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(http_status_code=201)
        mock_logger.debug.assert_called_with(
            "GitLab commit status created for project.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService._get_repo_id")
    def test_send_build_status_404_error(self, repo_id, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 404
        repo_id.return_value = "9999"

        success = self.service.send_build_status(
            build=self.external_build,
            commit=self.external_build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        self.assertFalse(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(http_status_code=404)
        mock_logger.info.assert_called_with(
            "GitLab project does not exist or user does not have permissions.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService._get_repo_id")
    def test_send_build_status_value_error(self, repo_id, session, mock_logger, mock_structlog):
        session.post.side_effect = ValueError
        repo_id().return_value = "9999"

        success = self.service.send_build_status(
            build=self.external_build,
            commit=self.external_build.commit,
            status=BUILD_STATUS_SUCCESS,
        )

        self.assertFalse(success)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            commit_status="success",
            user_username=self.user.username,
            url=mock.ANY,
        )
        mock_logger.exception.assert_called_with(
            "GitLab commit status creation failed.",
            debug_data=None,
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    def test_setup_webhook_successful(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 201
        session.post.return_value.json.return_value = {}
        success = self.service.setup_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            http_status_code=201,
        )
        mock_logger.debug.assert_called_with(
            "GitLab webhook creation successful for project.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    def test_setup_webhook_404_error(self, session, mock_logger, mock_structlog):
        session.post.return_value.status_code = 404
        success = self.service.setup_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertFalse(success)
        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(http_status_code=404)
        mock_logger.info.assert_called_with(
            "Gitlab project does not exist or user does not have permissions.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    def test_setup_webhook_value_error(self, session, mock_logger, mock_structlog):
        session.post.side_effect = ValueError
        self.service.setup_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
            url="https://gitlab.com/api/v4/projects/testorga%2Ftestrepo/hooks",
        )
        mock_logger.exception.assert_called_with(
            "GitLab webhook creation failed.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService._get_repo_id")
    def test_update_webhook_successful(self, repo_id, session, mock_logger, mock_structlog):
        repo_id.return_value = "9999"
        session.put.return_value.status_code = 200
        session.put.return_value.json.return_value = {}
        success = self.service.update_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertTrue(success)
        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.info.assert_called_with(
            "GitLab webhook update successful for project.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.setup_webhook")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService._get_repo_id")
    def test_update_webhook_404_error(self, repo_id, setup_webhook, session):
        repo_id.return_value = "9999"
        session.put.return_value.status_code = 404
        self.service.update_webhook(self.project, self.integration)

        setup_webhook.assert_called_once_with(self.project, self.integration)

    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.setup_webhook")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService._get_repo_id")
    def test_update_webhook_no_provider_data(self, repo_id, setup_webhook, session):
        self.integration.provider_data = {}
        self.integration.save()

        repo_id.return_value = "9999"
        session.put.side_effect = AttributeError
        self.service.update_webhook(self.project, self.integration)

        setup_webhook.assert_called_once_with(self.project, self.integration)

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService._get_repo_id")
    def test_update_webhook_value_error(self, repo_id, session, mock_logger, mock_structlog):
        repo_id.return_value = "9999"
        session.put.side_effect = ValueError
        self.service.update_webhook(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertIsNotNone(self.integration.secret)
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.exception.assert_called_with(
            "GitLab webhook update failed.",
            debug_data=None,
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    def test_get_provider_data_successful(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        webhook_data = self.provider_data
        rtd_webhook_url = "https://{domain}{path}".format(
            domain=settings.PRODUCTION_DOMAIN,
            path=reverse(
                "api_webhook",
                kwargs={
                    "project_slug": self.project.slug,
                    "integration_pk": self.integration.pk,
                },
            ),
        )
        webhook_data[0]["url"] = rtd_webhook_url

        session.get.return_value.status_code = 200
        session.get.return_value.json.return_value = webhook_data

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, webhook_data[0])
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.info.assert_called_with(
            "GitLab integration updated with provider data for project.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    def test_get_provider_data_404_error(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        session.get.return_value.status_code = 404

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.info.assert_called_with(
            "GitLab project does not exist or user does not have permissions.",
        )

    @mock.patch("readthedocs.oauth.services.gitlab.structlog")
    @mock.patch("readthedocs.oauth.services.gitlab.log")
    @mock.patch("readthedocs.oauth.services.gitlab.GitLabService.session")
    def test_get_provider_data_attribute_error(self, session, mock_logger, mock_structlog):
        self.integration.provider_data = {}
        self.integration.save()

        session.get.side_effect = AttributeError

        self.service.get_provider_data(self.project, self.integration)

        self.integration.refresh_from_db()

        self.assertEqual(self.integration.provider_data, {})
        mock_structlog.contextvars.bind_contextvars.assert_called_with(
            project_slug=self.project.slug,
            integration_id=self.integration.pk,
        )
        mock_logger.exception.assert_called_with(
            "GitLab webhook Listing failed for project.",
        )

    def test_project_moved_from_user_to_group(self):
        repo = self.service.create_repository(self.repo_response_data)
        assert repo.organization is None
        assert repo.full_name == "testorga/testrepo"
        assert not repo.private
        assert repo.remote_repository_relations.count() == 1
        relationship = repo.remote_repository_relations.first()
        assert relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

        self.repo_response_data["namespace"] = {
            "kind": "group",
            "name": "Test Orga",
            "path": "testorga",
            "id": self.org.remote_id,
            "full_path": self.org.slug,
        }
        repo_b = self.service.create_repository(self.repo_response_data)
        assert repo_b == repo
        repo.refresh_from_db()
        assert repo.organization == self.org
        relationship = repo.remote_repository_relations.first()
        assert relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

    def test_project_moved_from_group_to_user(self):
        self.repo_response_data["namespace"] = {
            "kind": "group",
            "name": "Test Orga",
            "path": "testorga",
            "id": self.org.remote_id,
            "full_path": self.org.slug,
        }
        repo = self.service.create_repository(self.repo_response_data)
        assert repo.organization == self.org
        assert repo.full_name == "testorga/testrepo"
        assert not repo.private
        assert repo.remote_repository_relations.count() == 1
        relationship = repo.remote_repository_relations.first()
        assert relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

        self.repo_response_data["namespace"] = {
            "kind": "user",
            "name": "Test User",
            "path": "testuser",
            "id": 1,
            "full_path": "testuser",
        }
        repo_b = self.service.create_repository(self.repo_response_data)
        assert repo_b == repo
        repo.refresh_from_db()
        assert repo.organization is None
        relationship = repo.remote_repository_relations.first()
        assert relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

    def test_project_moved_between_groups(self):
        self.repo_response_data["namespace"] = {
            "kind": "group",
            "name": "Test Orga",
            "path": "testorga",
            "id": self.org.remote_id,
            "full_path": self.org.slug,
        }
        repo = self.service.create_repository(self.repo_response_data)
        assert repo.organization == self.org
        assert repo.full_name == "testorga/testrepo"
        assert not repo.private
        assert repo.remote_repository_relations.count() == 1
        relationship = repo.remote_repository_relations.first()
        assert relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

        self.repo_response_data["namespace"] = {
            "kind": "group",
            "name": "Another Group",
            "path": "anothergroup",
            "id": "2",
            "full_path": "anothergroup",
        }

        repo_b = self.service.create_repository(self.repo_response_data)
        assert repo_b == repo
        repo.refresh_from_db()
        another_group = RemoteOrganization.objects.get(
            remote_id="2",
            vcs_provider=GITLAB,
        )
        assert repo.organization == another_group
        relationship = repo.remote_repository_relations.first()
        assert relationship.admin
        assert relationship.user == self.user
        assert relationship.account == self.service.account

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository_gl(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=GITLAB,
            full_name="testorga/testrepo",
            remote_id=self.repo_response_data["id"],
        )
        assert not remote_repo.users.filter(id=self.user.id).exists()

        request.get(f"https://gitlab.com/api/v4/projects/{remote_repo.remote_id}", json=self.repo_response_data)
        self.service.update_repository(remote_repo)

        remote_repo.refresh_from_db()
        assert remote_repo.name == "testrepo"
        assert remote_repo.full_name == "testorga/testrepo"
        assert remote_repo.description == "Test Repo"
        assert remote_repo.users.filter(id=self.user.id).exists()
        relation = remote_repo.remote_repository_relations.get(user=self.user)
        assert relation.account == self.social_account
        assert relation.admin

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository_remove_user_relation(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=GITLAB,
            full_name="testorga/testrepo",
            remote_id=self.repo_response_data["id"],
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_account,
            remote_repository=remote_repo,
            admin=True,
        )
        assert remote_repo.users.filter(id=self.user.id).exists()

        request.get(f"https://gitlab.com/api/v4/projects/{remote_repo.remote_id}", status_code=404)
        self.service.update_repository(remote_repo)
        remote_repo.refresh_from_db()

        assert remote_repo.full_name == "testorga/testrepo"
        assert not remote_repo.description
        assert not remote_repo.users.filter(id=self.user.id).exists()

    @requests_mock.Mocker(kw="request")
    def test_update_remote_repository_remove_user_relation_public_repo(self, request):
        remote_repo = get(
            RemoteRepository,
            vcs_provider=GITLAB,
            full_name="testorga/testrepo",
            remote_id=self.repo_response_data["id"],
        )
        get(
            RemoteRepositoryRelation,
            user=self.user,
            account=self.social_account,
            remote_repository=remote_repo,
            admin=True,
        )
        assert remote_repo.users.filter(id=self.user.id).exists()

        for k in self.repo_response_data["permissions"]:
            self.repo_response_data["permissions"][k] = None

        request.get(f"https://gitlab.com/api/v4/projects/{remote_repo.remote_id}", json=self.repo_response_data)
        self.service.update_repository(remote_repo)
        remote_repo.refresh_from_db()

        assert remote_repo.name == "testrepo"
        assert remote_repo.full_name == "testorga/testrepo"
        assert remote_repo.description == "Test Repo"
        assert not remote_repo.users.filter(id=self.user.id).exists()
