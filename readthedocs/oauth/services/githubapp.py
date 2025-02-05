from functools import cached_property, lru_cache

import structlog
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from github import Auth, GithubIntegration
from github.Installation import Installation as GHInstallation
from github.Organization import Organization as GHOrganization
from github.Repository import Repository as GHRepository

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)

log = structlog.get_logger(__name__)


class GitHubAppClient:
    def __init__(self, installation_id: int):
        self.installation_id = installation_id

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
    def integration_client(self):
        """Return a client authenticated as the GitHub App to interact with the installation API"""
        return GithubIntegration(auth=self._get_auth())

    @cached_property
    def client(self):
        """Return a client authenticated as the GitHub App to interact with most of the GH API"""
        return self.integration_client.get_github_for_installation(self.installation_id)

    @cached_property
    def app_installation(self) -> GHInstallation:
        return self.integration_client.get_app_installation(self.installation_id)


class GitHubAppService:
    vcs_provider_slug = GITHUB

    def __init__(self, installation: GitHubAppInstallation):
        self.installation = installation
        self.gha_client = GitHubAppClient(self.installation.installation_id)

    def sync_repositories(self):
        return self._sync_installation_repositories()

    def _sync_installation_repositories(self):
        remote_repositories = []
        for repo in self.gha_client.app_installation.get_repos():
            remote_repo = self._create_or_update_repository_from_gh(repo)
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

    def update_or_create_repositories(self, repository_ids: list[int]):
        for repository_id in repository_ids:
            repo = self.gha_client.client.get_repo(repository_id)
            self._create_or_update_repository_from_gh(repo)

    def delete_repositories(self, repository_ids: list[int]):
        """
        Delete repositories from the given list that are not linked to a project.

        We don't remove repositories that are linked to a project, since a user could
        grant access to the repository again, and we don't want users having to manually
        link the project to the repository again.
        """
        # Extract all the organizations linked to these repositories,
        # so we can remove organizations that don't have any repositories
        # after removing the repositories.
        remote_organizations = RemoteOrganization.objects.filter(
            repositories__remote_id__in=repository_ids,
            vcs_provider=self.vcs_provider_slug,
        )

        RemoteRepository.objects.filter(
            github_app_installation=self.installation,
            vcs_provider=self.vcs_provider_slug,
            remote_id__in=repository_ids,
            projects=None,
        ).delete()

        # Delete organizations that don't have any repositories.
        remote_organizations.filter(repositories=None).delete()

    def delete_organization(self, organization_id: int):
        """
        Delete an organization and all its repositories from the database only if they are not linked to a project.
        """
        RemoteOrganization.objects.filter(
            remote_id=str(organization_id),
            vcs_provider=self.vcs_provider_slug,
            repositories__projects=None,
        ).delete()

    def _create_or_update_repository_from_gh(
        self, gh_repo: GHRepository
    ) -> RemoteRepository | None:
        # What about a project that is public, and then becomes private?
        # I think we should allow creating remote repositories for these,
        # but block import/clone and other operations.
        if not settings.ALLOW_PRIVATE_REPOS and gh_repo.private:
            return

        target_id = self.installation.target_id
        target_type = self.installation.target_type
        # NOTE: All the repositories should be owned by the installation account.
        # This should never happen, unless this assumption is wrong.
        if gh_repo.owner.id != target_id or gh_repo.owner.type != target_type:
            log.exception(
                "Repository owner does not match the installation account",
                repository_id=gh_repo.id,
                repository_owner_id=gh_repo.owner.id,
                installation_target_id=target_id,
                installation_target_type=target_type,
            )
            return

        remote_repo, _ = RemoteRepository.objects.get_or_create(
            remote_id=str(gh_repo.id),
            vcs_provider=self.vcs_provider_slug,
        )

        remote_repo.name = gh_repo.name
        remote_repo.full_name = gh_repo.full_name
        remote_repo.description = gh_repo.description
        remote_repo.avatar_url = gh_repo.owner.avatar_url
        remote_repo.ssh_url = gh_repo.ssh_url
        remote_repo.html_url = gh_repo.html_url
        remote_repo.private = gh_repo.private
        remote_repo.default_branch = gh_repo.default_branch

        # TODO: Do we need the SSH URL for private repositories now that we can clone using a token?
        remote_repo.clone_url = (
            gh_repo.ssh_url if gh_repo.private else gh_repo.clone_url
        )

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
        if gh_repo.owner.type == GitHubAccountType.ORGANIZATION:
            # NOTE: The owner object doesn't have all attributes of an organization,
            # so we need to fetch the organization object.
            gh_organization = self._get_gh_organization(gh_repo.owner.id)
            remote_repo.organization = self._create_or_update_organization_from_gh(
                gh_organization
            )

        remote_repo.save()
        self._resync_collaborators(gh_repo, remote_repo)
        return remote_repo

    # NOTE: normally, this should cache only one organization at a time, but just in case...
    @lru_cache(maxsize=50)
    def _get_gh_organization(self, org_id: int) -> GHOrganization:
        # NOTE: cast to str, since PyGithub expects a string,
        # even if the API accepts a string or an int.
        # TODO: send a PR upstream to fix this.
        return self.gha_client.client.get_organization(str(org_id))

    # NOTE: normally, this should cache only one organization at a time, but just in case...
    @lru_cache(maxsize=50)
    def _create_or_update_organization_from_gh(
        self, gh_org: GHOrganization
    ) -> RemoteOrganization:
        """
        Create or update a remote organization from a GitHub organization object.

        We also sync the members of the organization with the database.

        This method is cached, since we want to update the organization only once per sync of an installation.
        """
        remote_org, _ = RemoteOrganization.objects.get_or_create(
            remote_id=str(gh_org.id),
            vcs_provider=self.vcs_provider_slug,
        )
        remote_org.slug = gh_org.login
        remote_org.name = gh_org.name
        # NOTE: do we need the email of the organization?
        remote_org.email = gh_org.email
        remote_org.avatar_url = gh_org.avatar_url
        remote_org.url = gh_org.html_url
        remote_org.save()
        self._resync_organization_members(gh_org, remote_org)
        return remote_org

    def _resync_collaborators(
        self, gh_repo: GHRepository, remote_repo: RemoteRepository
    ):
        """
        Sync collaborators of a repository with the database.

        This method will remove collaborators that are no longer in the list.
        """
        collaborators = {
            collaborator.id: collaborator
            for collaborator in gh_repo.get_collaborators()
        }
        remote_repo_relations_ids = []
        for account in self._get_social_accounts(collaborators.keys()):
            remote_repo_relation, _ = RemoteRepositoryRelation.objects.get_or_create(
                remote_repository=remote_repo,
                user=account.user,
                account=account,
            )
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

    def update_or_create_organization(self, org_id: int) -> RemoteOrganization:
        gh_org = self._get_gh_organization(org_id)
        return self._create_or_update_organization_from_gh(gh_org)

    def _resync_organization_members(
        self, gh_org: GHOrganization, remote_org: RemoteOrganization
    ):
        """
        Sync members of an organization with the database.

        This method will remove members that are no longer in the list.
        """
        members = {member.id: member for member in gh_org.get_members()}
        remote_org_relations_ids = []
        for account in self._get_social_accounts(members.keys()):
            remote_org_relation, _ = RemoteOrganizationRelation.objects.get_or_create(
                remote_organization=remote_org,
                user=account.user,
                account=account,
            )
            remote_org_relations_ids.append(remote_org_relation.pk)

        # Remove members that are no longer in the list.
        RemoteOrganizationRelation.objects.filter(
            remote_organization=remote_org,
        ).exclude(
            pk__in=remote_org_relations_ids,
        ).delete()
