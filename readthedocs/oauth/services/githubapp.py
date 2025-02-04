from functools import cached_property

import structlog
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from github import Auth, GithubIntegration
from github.Installation import Installation as GHInstallation
from github.NamedUser import NamedUser as GHNamedUser
from github.Repository import Repository as GHRepository

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteOrganization,
    RemoteRepository,
    RemoteRepositoryRelation,
)

log = structlog.get_logger(__name__)


class GitHubAppService:
    vcs_provider_slug = GITHUB

    def __init__(self, installation: GitHubAppInstallation):
        self.installation = installation

    def _get_auth(self):
        app_auth = Auth.AppAuth(
            app_id=settings.GITHUB_APP_CLIENT_ID,
            private_key=settings.GITHUB_APP_PRIVATE_KEY,
            # 10 minutes is the maximum allowed by GitHub.
            # PyGithub will handle the token expiration and renew it automatically.
            jwt_expiry=60 * 10,
        )
        return app_auth

    @cached_property
    def client(self):
        """Return a client authenticated as the GitHub App to interact with most of the GH API"""
        return self.integration_client.get_github_for_installation(
            self.installation.installation_id
        )

    @cached_property
    def integration_client(self):
        """Return a client authenticated as the GitHub App to interact with the installation API"""
        return GithubIntegration(auth=self._get_auth())

    @cached_property
    def app_installation(self) -> GHInstallation:
        return self.integration_client.get_app_installation(
            self.installation.installation_id
        )

    def sync_repositories(self):
        # if self.installation.target_type != GitHubAccountType.USER:
        #     return
        return self._sync_installation_repositories()

    def _sync_installation_repositories(self):
        remote_repositories = []
        for repo in self.app_installation.get_repos():
            remote_repo = self.create_or_update_repository(repo)
            if remote_repo:
                remote_repositories.append(remote_repo)

        # Remove repositories that are no longer in the list,
        # and that are not linked to a project.
        RemoteRepository.objects.filter(
            github_app_installation=self.installation,
            vcs_provider=self.vcs_provider_slug,
            projects=None,
        ).exclude(
            pk__in=[repo.pk for repo in remote_repositories],
        ).delete()

    def add_repositories(self, repository_ids: list[int]):
        for repository_id in repository_ids:
            repo = self.client.get_repo(repository_id)
            self.create_or_update_repository(repo)

    def remove_repositories(self, repository_ids: list[int]):
        """
        Remove repositories from the given list that are not linked to a project.

        We don't remove repositories that are linked to a project, since a user could
        grant access to the repository again, and we don't want users having to manually
        link the project to the repository again.
        """
        RemoteRepository.objects.filter(
            github_app_installation=self.installation,
            vcs_provider=self.vcs_provider_slug,
            remote_id__in=repository_ids,
            projects=None,
        ).delete()

    def create_or_update_repository(
        self, repo: GHRepository
    ) -> RemoteRepository | None:
        if not settings.ALLOW_PRIVATE_REPOS and repo.private:
            return

        target_id = self.installation.target_id
        target_type = self.installation.target_type
        # NOTE: All the repositories should be owned by the installation account.
        # This should never happen, unless this assumption is wrong.
        if repo.owner.id != target_id or repo.owner.type != target_type:
            log.exception(
                "Repository owner does not match the installation account",
                repository_id=repo.id,
                repository_owner_id=repo.owner.id,
                installation_target_id=target_id,
                installation_target_type=target_type,
            )
            return

        remote_repo, _ = RemoteRepository.objects.get_or_create(
            remote_id=str(repo.id),
            vcs_provider=self.vcs_provider_slug,
        )

        remote_repo.name = repo.name
        remote_repo.full_name = repo.full_name
        remote_repo.description = repo.description
        remote_repo.avatar_url = repo.owner.avatar_url
        remote_repo.ssh_url = repo.ssh_url
        remote_repo.html_url = repo.html_url
        remote_repo.private = repo.private
        remote_repo.default_branch = repo.default_branch

        # TODO: Do we need the SSH URL for private repositories now that we can clone using a token?
        remote_repo.clone_url = repo.ssh_url if repo.private else repo.clone_url

        # NOTE: Only one installation of our APP should give access to a repository.
        # This should only happen if our data is out of sync.
        if (
            remote_repo.github_app_installation
            and remote_repo.github_app_installation != self.installation
        ):
            log.info(
                "Repository linked to another installation",
                repository_id=remote_repo.remote_id,
                old_installation_id=remote_repo.github_app_installation.installation_id,
                new_installation_id=self.installation.installation_id,
            )
        remote_repo.github_app_installation = self.installation

        remote_repo.organization = None
        if repo.owner.type == GitHubAccountType.ORGANIZATION:
            remote_repo.organization = self.create_or_update_organization(repo.owner)

        self._resync_collaborators(repo, remote_repo)
        # What about members of the organization? Do we care?
        # I think all of our permissions are based on the collaborators of the repository,
        # not the members of the organization.
        remote_repo.save()
        return remote_repo

    def create_or_update_organization(self, org: GHNamedUser) -> RemoteOrganization:
        remote_org, _ = RemoteOrganization.objects.get_or_create(
            remote_id=str(org.id),
            vcs_provider=self.vcs_provider_slug,
        )
        remote_org.slug = org.login
        remote_org.name = org.name
        # NOTE: do we need the email of the organization?
        remote_org.email = org.email
        remote_org.avatar_url = org.avatar_url
        remote_org.url = org.html_url
        remote_org.save()
        return remote_org

    def _resync_collaborators(self, repo: GHRepository, remote_repo: RemoteRepository):
        """
        Sync collaborators of a repository with the database.

        This method will remove collaborators that are no longer in the list.
        """
        collaborators = {
            collaborator.id: collaborator
            # Return all collaborators or just the ones with admin permission?
            for collaborator in repo.get_collaborators()
        }
        remote_repo_relations_ids = []
        for account in self._get_social_accounts(collaborators.keys()):
            remote_repo_relation, _ = RemoteRepositoryRelation.objects.get_or_create(
                remote_repository=remote_repo,
                user=account.user,
                account=account,
            )
            remote_repo_relation.user = account.user
            remote_repo_relation.admin = collaborators[
                int(account.uid)
            ].permissions.admin
            remote_repo_relation.save()
            remote_repo_relations_ids.append(remote_repo_relation.pk)

        # Remove collaborators that are no longer in the list.
        RemoteRepositoryRelation.objects.filter(
            remote_repository=remote_repo,
        ).exclude(
            pk__in=remote_repo_relations_ids,
        ).delete()

    def _get_social_accounts(self, ids):
        return SocialAccount.objects.filter(
            uid__in=ids,
            provider=GitHubAppProvider.id,
        ).select_related("user")

    def sync_organizations(self):
        if self.installation.target_type != GitHubAccountType.ORGANIZATION:
            return
        return self._sync_installation_repositories()
