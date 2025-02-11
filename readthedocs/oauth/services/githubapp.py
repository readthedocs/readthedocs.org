from functools import cached_property, lru_cache

import structlog
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from github import Github
from github.Installation import Installation as GHInstallation
from github.Organization import Organization as GHOrganization
from github.Repository import Repository as GHRepository

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS, SELECT_BUILD_STATUS
from readthedocs.oauth.clients import get_gh_app_client, get_oauth2_client
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.models import (
    GitHubAccountType,
    GitHubAppInstallation,
    RemoteOrganization,
    RemoteOrganizationRelation,
    RemoteRepository,
    RemoteRepositoryRelation,
)
from readthedocs.oauth.services.base import Service

log = structlog.get_logger(__name__)


class GitHubAppService(Service):
    vcs_provider_slug = GITHUB
    allauth_provider = GitHubAppProvider

    def __init__(self, installation: GitHubAppInstallation):
        self.installation = installation
        self.gha_client = get_gh_app_client()

    @cached_property
    def app_installation(self) -> GHInstallation:
        """
        Return the installation object from the GitHub API.

        Usefull to interact with installation related endpoints.
        """
        return self.gha_client.get_app_installation(
            self.installation.installation_id,
        )

    @cached_property
    def installation_client(self) -> Github:
        """Return a client authenticated as the GitHub installation to interact with the GH API."""
        return self.gha_client.get_github_for_installation(
            self.installation.installation_id
        )

    @classmethod
    def for_project(cls, project):
        """
        Return a GitHubAppService for the installation linked to the project.

        Since this service only works for projects that have a remote repository,
        and are linked to a GitHub App installation,
        this returns only one service or None.
        """
        if (
            not project.remote_repository
            or not project.remote_repository.github_app_installation
        ):
            return None

        yield cls(project.remote_repository.github_app_installation)

    @classmethod
    def for_user(cls, user):
        """
        Return a GitHubAppService for each installation accessible to the user.

        In order to get the installations accessible to the user, we need to use
        the GitHub API authenticated as the user, making use of the user's access token
        (not the installation token).

        See:

        - https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-with-a-github-app-on-behalf-of-a-user
        - https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app
        - https://docs.github.com/en/rest/apps/installations?apiVersion=2022-11-28#list-app-installations-accessible-to-the-user-access-token

        .. note::

           If the installation wasn't in our database, we create it
           (but we don't sync the repositories, since the caller should be responsible for that).

        .. note::

           User access tokens expire after 8 hours, but our OAuth2 client should handle refreshing the token.
           But, the refresh token expires after 6 months, in order to refresh that token,
           the user needs to sign in using GitHub again (just a normal sing-in, not a re-authorization or sign-up).
        """
        social_accounts = SocialAccount.objects.filter(
            user=user,
            provider=cls.allauth_provider.id,
        )
        for account in social_accounts:
            oauth2_client = get_oauth2_client(account)
            resp = oauth2_client.get("https://api.github.com/user/installations")

            if resp.status_code != 200:
                continue

            for gh_installation in resp.json()["installations"]:
                installation = GitHubAppInstallation.objects.get_or_create_installation(
                    installation_id=gh_installation["id"],
                    target_id=gh_installation["target_id"],
                    target_type=gh_installation["target_type"],
                    extra_data={"installation": gh_installation},
                ).first()
                if installation:
                    yield cls(installation)

    def sync(self):
        """
        Sync all repositories and organizations that are accessible to the installation.

        Repositories that are no longer accessible to the installation are removed from the database
        only if they are not linked to a project. This is in case the user wants to grant access to the repository again.

        If a remote organization doesn't have any repositories after removing the repositories,
        we remove the organization from the database.
        """
        remote_repositories = []
        for repo in self.app_installation.get_repos():
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
        """Update or create repositories from the given list of repository IDs."""
        for repository_id in repository_ids:
            repo = self.installation_client.get_repo(repository_id)
            self._create_or_update_repository_from_gh(repo)

    def delete_repositories(self, repository_ids: list[int]):
        """
        Delete repositories from the given list that are not linked to a project.

        We don't remove repositories that are linked to a project, since a user could
        grant access to the repository again, and we don't want users having to manually
        link the project to the repository again.

        We also remove organizations that don't have any repositories after removing the repositories.
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
        """Delete an organization and all its repositories from the database only if they are not linked to a project."""
        RemoteOrganization.objects.filter(
            remote_id=str(organization_id),
            vcs_provider=self.vcs_provider_slug,
            repositories__projects=None,
        ).delete()

    def _create_or_update_repository_from_gh(
        self, gh_repo: GHRepository
    ) -> RemoteRepository | None:
        """
        Create or update a remote repository from a GitHub repository object.

        We also sync the collaborators of the repository with the database,
        and create or update the organization of the repository.
        """
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
        remote_repo.avatar_url = (
            gh_repo.owner.avatar_url or self.default_user_avatar_url
        )
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
        """Get a GitHub organization object given its numeric ID."""
        # NOTE: cast to str, since PyGithub expects a string,
        # even if the API accepts a string or an int.
        # TODO: send a PR upstream to fix this.
        return self.installation_client.get_organization(str(org_id))

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
        remote_org.avatar_url = gh_org.avatar_url or self.default_org_avatar_url
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
            provider=self.allauth_provider.id,
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

    def send_build_status(self, *, build, commit, status):
        project = build.project
        remote_repo = project.remote_repository

        if status == BUILD_STATUS_SUCCESS:
            target_url = build.version.get_absolute_url()
        else:
            target_url = build.get_full_url()

        state = SELECT_BUILD_STATUS[status]["github"]
        description = SELECT_BUILD_STATUS[status]["description"]
        context = f"{settings.RTD_BUILD_STATUS_API_NAME}:{project.slug}"

        gh_repo = self.installation_client.get_repo(int(remote_repo.remote_id))
        gh_repo.get_commit(commit).create_status(
            state=state,
            target_url=target_url,
            description=description,
            context=context,
        )

    def get_clone_token(self, project):
        """
        Return a token for HTTP Git clone access to the repository.

        See:

        - https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation
        - https://docs.github.com/en/rest/apps/apps?apiVersion=2022-11-28#create-an-installation-access-token-for-an-app
        """
        # TODO: we can pass the repository_ids to get a token with access to specific repositories.
        # We should upstream this feature to PyGithub.
        # We can also pass a specific permissions object to get a token with specific permissions
        # if we want to scope this token even more.
        access_token = self.gha_client.get_access_token(
            self.installation.installation_id
        )
        return f"x-access-token:{access_token.token}"

    def setup_webhook(self, project, integration=None):
        """When using a GitHub App, we don't need to set up a webhook."""
        return True

    def update_webhook(self, project, integration=None):
        """When using a GitHub App, we don't need to set up a webhook."""
        return True
