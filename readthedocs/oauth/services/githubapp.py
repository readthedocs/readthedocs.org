from functools import cached_property
from functools import lru_cache
from itertools import groupby

import structlog
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from github import Github
from github import GithubException
from github.Installation import Installation as GHInstallation
from github.Organization import Organization as GHOrganization
from github.Repository import Repository as GHRepository

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.builds.constants import BUILD_STATUS_SUCCESS
from readthedocs.builds.constants import SELECT_BUILD_STATUS
from readthedocs.oauth.clients import get_gh_app_client
from readthedocs.oauth.clients import get_oauth2_client
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAccountType
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.oauth.models import RemoteOrganization
from readthedocs.oauth.models import RemoteOrganizationRelation
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.models import RemoteRepositoryRelation
from readthedocs.oauth.services.base import Service
from readthedocs.oauth.services.base import SyncServiceError


log = structlog.get_logger(__name__)


class GitHubAppService(Service):
    vcs_provider_slug = GITHUB_APP
    allauth_provider = GitHubAppProvider
    supports_build_status = True
    supports_clone_token = True
    supports_commenting = True

    def __init__(self, installation: GitHubAppInstallation):
        self.installation = installation

    @cached_property
    def gh_app_client(self):
        return get_gh_app_client()

    @lru_cache
    def get_app_installation(self) -> GHInstallation:
        """
        Return the installation object from the GitHub API.

        Useful to interact with installation related endpoints.

        If the installation is no longer accessible, this will raise a GithubException.
        """
        return self.gh_app_client.get_app_installation(
            self.installation.installation_id,
        )

    @cached_property
    def installation_client(self) -> Github:
        """Return a client authenticated as the GitHub installation to interact with the GH API."""
        return self.gh_app_client.get_github_for_installation(self.installation.installation_id)

    @classmethod
    def for_project(cls, project):
        """
        Return a GitHubAppService for the installation linked to the project.

        Since this service only works for projects that have a remote repository,
        and are linked to a GitHub App installation,
        this returns only one service or None.
        """
        if not project.remote_repository or not project.remote_repository.github_app_installation:
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
           the user needs to sign in using GitHub again (just a normal sign in, not a re-authorization or sign-up).
        """
        social_accounts = SocialAccount.objects.filter(
            user=user,
            provider=cls.allauth_provider.id,
        )
        for account in social_accounts:
            oauth2_client = get_oauth2_client(account)
            resp = oauth2_client.get("https://api.github.com/user/installations")
            if resp.status_code != 200:
                log.info(
                    "Failed to fetch installations from GitHub",
                    user=user,
                    account_id=account.uid,
                    status_code=resp.status_code,
                    response=resp.json(),
                )
                continue

            for gh_installation in resp.json()["installations"]:
                (
                    installation,
                    _,
                ) = GitHubAppInstallation.objects.get_or_create_installation(
                    installation_id=gh_installation["id"],
                    target_id=gh_installation["target_id"],
                    target_type=gh_installation["target_type"],
                    extra_data={"installation": gh_installation},
                )
                yield cls(installation)

    @classmethod
    def sync_user_access(cls, user):
        """
        Sync the user's access to the provider repositories and organizations.

        Since we are using a GitHub App, we don't have a way to check all the repositories and organizations
        the user has access to or if it lost access to a repository or organization.

        Our webhooks should keep permissions in sync, but just in case,
        we first sync the repositories from all installations accessible to the user (refresh access to new repositories),
        and then we sync each repository the user has access to (check if the user lost access to a repository, or his access level changed).

        This method is called when the user logs in or when the user manually clicks on "Sync repositories".
        """
        has_error = False
        # Refresh access to all installations accessible to the user.
        for service in cls.for_user(user):
            try:
                service.sync()
            except SyncServiceError:
                # Don't stop the sync if one installation fails,
                # as we should try to sync all installations.
                has_error = True

        # Update the access to each repository the user has access to.
        queryset = RemoteRepository.objects.filter(
            remote_repository_relations__user=user,
            vcs_provider=cls.vcs_provider_slug,
        ).select_related("github_app_installation")
        # Group by github_app_installation, so we don't create multiple clients.
        grouped_installations = groupby(
            queryset,
            key=lambda x: x.github_app_installation,
        )
        for installation, remote_repos in grouped_installations:
            service = cls(installation)
            service.update_or_create_repositories(
                [int(remote_repo.remote_id) for remote_repo in remote_repos]
            )

        # Update access to each organization the user has access to.
        queryset = RemoteOrganization.objects.filter(
            remote_organization_relations__user=user,
            vcs_provider=cls.vcs_provider_slug,
        )
        for remote_organization in queryset:
            remote_repo = remote_organization.repositories.select_related(
                "github_app_installation"
            ).first()
            # NOTE: this should never happen, unless our data is out of sync
            # (we delete orphaned organizations when deleting projects).
            if not remote_repo:
                log.info(
                    "Remote organization without repositories detected, deleting.",
                    organization_login=remote_organization.slug,
                    remote_id=remote_organization.remote_id,
                )
                remote_organization.delete()
                continue

            service = cls(remote_repo.github_app_installation)
            service.update_or_create_organization(remote_organization.slug)

        if has_error:
            raise SyncServiceError()

    def sync(self):
        """
        Sync all repositories and organizations that are accessible to the installation.

        Repositories that are no longer accessible to the installation are removed from the database
        only if they are not linked to a project. This is in case the user wants to grant access to the repository again.

        If a remote organization doesn't have any repositories after removing the repositories,
        we remove the organization from the database.
        """
        try:
            app_installation = self.get_app_installation()
        except GithubException as e:
            log.info(
                "Failed to get installation",
                installation_id=self.installation.installation_id,
                exc_info=True,
            )
            if e.status == 404:
                # The app was uninstalled, we remove the installation from the database.
                self.installation.delete()
            raise SyncServiceError()

        if app_installation.suspended_at is not None:
            log.info(
                "Installation is suspended",
                installation_id=self.installation.installation_id,
                suspended_at=app_installation.suspended_at,
            )
            # The installation is suspended, we don't have access to it anymore,
            # so we just delete it from the database.
            self.installation.delete()
            raise SyncServiceError()

        remote_repositories = []
        for gh_repo in app_installation.get_repos():
            remote_repo = self._create_or_update_repository_from_gh(gh_repo)
            if remote_repo:
                remote_repositories.append(remote_repo)

        repos_to_delete = self.installation.repositories.exclude(
            pk__in=[repo.pk for repo in remote_repositories],
        ).values_list("remote_id", flat=True)
        self.installation.delete_repositories(repos_to_delete)

    def update_repository(self, remote_repository: RemoteRepository):
        """
        Update a single repository from the given remote repository.

        .. note::

           Unlike the other providers, this method doesn't update the
           `remote_repository` object itself. If you need the updated object,
           fetch it again from the database.
        """
        self.update_or_create_repositories([remote_repository.remote_id])

    def update_or_create_repositories(self, repository_ids: list[int]):
        """Update or create repositories from the given list of repository IDs."""
        repositories_to_delete = []
        for repository_id in repository_ids:
            try:
                # NOTE: we save the repository ID as a string in our database,
                # in order for PyGithub to use the API to fetch the repository by ID (not by name).
                # it needs to be an integer, so just in case we cast it to an integer.
                repo = self.installation_client.get_repo(int(repository_id))

                # GitHub will send some events from all repositories in the organization (like the members event),
                # even from those that don't have the app installed. For private repositories, the previous API
                # call will fail, but for public repositories we can still hit the API successfully, so we make
                # an additional check using the GitHub App API, which will raise a GithubException with a 404
                # status code if the app is not installed on the repository.
                if not repo.private:
                    self.gh_app_client.get_repo_installation(owner=repo.owner.login, repo=repo.name)
            except GithubException as e:
                log.info(
                    "Failed to fetch repository from GitHub",
                    repository_id=repository_id,
                    exc_info=True,
                )
                # if we lost access to the repository,
                # we remove the repository from the database,
                # and clean up the collaborators and relations.
                if e.status in [404, 403]:
                    repositories_to_delete.append(repository_id)
                continue
            self._create_or_update_repository_from_gh(repo)

        if repositories_to_delete:
            self.installation.delete_repositories(repositories_to_delete)

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
        # The following condition should never happen, unless the previous assumption is wrong.
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
        remote_repo.avatar_url = gh_repo.owner.avatar_url or self.default_user_avatar_url
        remote_repo.ssh_url = gh_repo.ssh_url
        remote_repo.html_url = gh_repo.html_url
        remote_repo.private = gh_repo.private
        remote_repo.default_branch = gh_repo.default_branch
        remote_repo.clone_url = gh_repo.clone_url

        # NOTE: Only one installation of our APP should give access to a repository.
        # The following condition should only happen if our data is out of sync.
        if (
            remote_repo.github_app_installation
            and remote_repo.github_app_installation != self.installation
        ):
            log.info(
                "Repository linked to another installation. Our data may be out of sync.",
                repository_id=remote_repo.remote_id,
                old_installation_id=remote_repo.github_app_installation.installation_id,
                new_installation_id=self.installation.installation_id,
            )
        remote_repo.github_app_installation = self.installation

        remote_repo.organization = None
        if gh_repo.owner.type == GitHubAccountType.ORGANIZATION:
            # NOTE: The owner object doesn't have all attributes of an organization,
            # so we need to fetch the organization object.
            remote_repo.organization = self.update_or_create_organization(gh_repo.owner.login)

        remote_repo.save()
        self._resync_collaborators(gh_repo, remote_repo)
        return remote_repo

    # NOTE: normally, this should cache only one organization at a time, but just in case...
    @lru_cache(maxsize=50)
    def _get_gh_organization(self, login: str) -> GHOrganization:
        """Get a GitHub organization object given its login identifier."""
        return self.installation_client.get_organization(login)

    # NOTE: normally, this should cache only one organization at a time, but just in case...
    @lru_cache(maxsize=50)
    def update_or_create_organization(self, login: str) -> RemoteOrganization:
        """
        Create or update a remote organization from its login identifier.

        We also sync the members of the organization with the database.
        This doesn't sync the repositories of the organization,
        since the installation is the one that lists the repositories it has access to.

        This method is cached, since we need to update the organization only once per sync of an installation.
        """
        gh_org = self._get_gh_organization(login)
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

    def _resync_collaborators(self, gh_repo: GHRepository, remote_repo: RemoteRepository):
        """
        Sync collaborators of a repository with the database.

        This method will remove collaborators that are no longer in the list.

        See https://docs.github.com/en/rest/collaborators/collaborators?apiVersion=2022-11-28#list-repository-collaborators.
        """
        collaborators = {
            collaborator.id: collaborator for collaborator in gh_repo.get_collaborators()
        }
        remote_repo_relations_ids = []
        for account in self._get_social_accounts(collaborators.keys()):
            remote_repo_relation, _ = RemoteRepositoryRelation.objects.get_or_create(
                remote_repository=remote_repo,
                user=account.user,
                account=account,
            )
            remote_repo_relation.admin = collaborators[int(account.uid)].permissions.admin
            remote_repo_relation.save()
            remote_repo_relations_ids.append(remote_repo_relation.pk)

        # Remove collaborators that are no longer in the list.
        RemoteRepositoryRelation.objects.filter(
            remote_repository=remote_repo,
        ).exclude(
            pk__in=remote_repo_relations_ids,
        ).delete()

    def _get_social_accounts(self, ids):
        """Get social accounts given a list of GitHub user IDs."""
        return SocialAccount.objects.filter(
            uid__in=ids,
            provider=self.allauth_provider.id,
        ).select_related("user")

    def _resync_organization_members(self, gh_org: GHOrganization, remote_org: RemoteOrganization):
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
        """
        Create a commit status on GitHub for the given build.

        See https://docs.github.com/en/rest/commits/statuses?apiVersion=2022-11-28#create-a-commit-status.
        """
        project = build.project
        remote_repo = project.remote_repository

        if status == BUILD_STATUS_SUCCESS:
            target_url = build.version.get_absolute_url()
        else:
            target_url = build.get_full_url()

        state = SELECT_BUILD_STATUS[status]["github"]
        description = SELECT_BUILD_STATUS[status]["description"]
        context = f"{settings.RTD_BUILD_STATUS_API_NAME}:{project.slug}"

        try:
            # NOTE: we use the lazy option to avoid fetching the repository object,
            # since we only need the object to interact with the commit status API.
            gh_repo = self.installation_client.get_repo(int(remote_repo.remote_id), lazy=True)
            gh_repo.get_commit(commit).create_status(
                state=state,
                target_url=target_url,
                description=description,
                context=context,
            )
            return True
        except GithubException:
            log.info(
                "Failed to send build status to GitHub",
                project=project.slug,
                build=build.pk,
                commit=commit,
                status=status,
                exc_info=True,
            )
            return False

    def get_clone_token(self, project):
        """
        Return a token for HTTP-based Git access to the repository.

        The token is scoped to have read-only access to the content of the repository attached to the project.
        The token expires after one hour (this is given by GitHub and can't be changed).

        See:
        - https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation
        - https://docs.github.com/en/rest/apps/apps?apiVersion=2022-11-28#create-an-installation-access-token-for-an-app
        """
        try:
            # TODO: Use self.gh_app_client.get_access_token instead,
            # once https://github.com/PyGithub/PyGithub/pull/3287 is merged.
            _, response = self.gh_app_client.requester.requestJsonAndCheck(
                "POST",
                f"/app/installations/{self.installation.installation_id}/access_tokens",
                headers=self.gh_app_client._get_headers(),
                input={
                    "repository_ids": [int(project.remote_repository.remote_id)],
                    "permissions": {
                        "contents": "read",
                    },
                },
            )
            token = response["token"]
            return f"x-access-token:{token}"
        except GithubException:
            log.info(
                "Failed to get clone token for project",
                installation_id=self.installation.installation_id,
                project=project.slug,
                exc_info=True,
            )
            return None

    def setup_webhook(self, project, integration=None) -> bool:
        """When using a GitHub App, we don't need to set up a webhook."""
        return True

    def update_webhook(self, project, integration=None) -> bool:
        """When using a GitHub App, we don't need to set up a webhook."""
        return True

    def post_comment(self, build, comment: str, create_new: bool = True):
        """
        Post a comment on the pull request attached to the build.

        Since repositories can be linked to multiple projects, we post a comment per project.
        We use an HTML comment to identify the comment for the project.
        """
        project = build.project
        version = build.version

        if not version.is_external:
            raise ValueError("Only versions from pull requests can have comments posted.")

        remote_repo = project.remote_repository
        # NOTE: we use the lazy option to avoid fetching the repository object,
        # since we only need the object to interact with the commit status API.
        gh_repo = self.installation_client.get_repo(int(remote_repo.remote_id), lazy=True)
        gh_issue = gh_repo.get_issue(int(version.verbose_name))
        existing_gh_comment = None
        comment_marker = f"<!-- readthedocs-{project.pk} -->"
        for gh_comment in gh_issue.get_comments():
            # Get the comment where the author is us, and the comment belongs to the project.
            # The login of the author is the name of the GitHub App, with the "[bot]" suffix.
            if (
                gh_comment.user.login == f"{settings.GITHUB_APP_NAME}[bot]"
                and comment_marker in gh_comment.body
            ):
                existing_gh_comment = gh_comment
                break

        comment = f"{comment_marker}\n{comment}"
        if existing_gh_comment:
            existing_gh_comment.edit(body=comment)
        elif create_new:
            gh_issue.create_comment(body=comment)
        else:
            log.debug(
                "No comment to update, skipping commenting",
                project=project.slug,
                build=build.pk,
            )
