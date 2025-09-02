"""This module contains the logic to help users migrate from the GitHub OAuth App to the GitHub App."""

from dataclasses import dataclass
from functools import cached_property
from typing import Iterator
from urllib.parse import urlencode

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.core.permissions import AdminPermission
from readthedocs.integrations.models import Integration
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAccountType
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.services import GitHubAppService
from readthedocs.oauth.services import GitHubService
from readthedocs.projects.models import Project


@dataclass
class GitHubAccountTarget:
    """Information about a GitHub account that is used as a target where to install the GitHub App."""

    id: int
    login: str
    type: GitHubAccountType
    avatar_url: str
    profile_url: str

    @cached_property
    def has_installation(self) -> bool:
        """Check if the GitHub App is installed in this account."""
        return GitHubAppInstallation.objects.filter(
            target_id=self.id, target_type=self.type
        ).exists()


@dataclass
class InstallationTargetGroup:
    """Group of repositories that should be installed in the same target (user or organization)."""

    target: GitHubAccountTarget
    repository_ids: set[int]

    @property
    def link(self):
        """
        Create a link to install the GitHub App on the target with the required repositories pre-selected.

        See https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/migrating-oauth-apps-to-github-apps#prompt-users-to-install-your-github-app.
        """
        base_url = (
            f"https://github.com/apps/{settings.GITHUB_APP_NAME}/installations/new/permissions"
        )
        query_params = urlencode(
            {
                "suggested_target_id": self.target.id,
                "repository_ids[]": self.repository_ids,
            },
            doseq=True,
        )
        return f"{base_url}?{query_params}"

    @property
    def installed(self):
        """
        Check if the app has been installed in all required repositories.

        If the the list of `repository_ids` is not empty, it means that the app still needs to be installed in some repositories,
        or that the app hasn't been installed at all in the target account.
        """
        return not bool(self.repository_ids)


@dataclass
class MigrationTarget:
    """Information about an individual project that needs to be migrated."""

    project: Project
    has_installation: bool
    is_admin: bool
    target_id: int

    @property
    def installation_link(self):
        """
        Create a link to install the GitHub App on the target repository.

        See https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/migrating-oauth-apps-to-github-apps
        """
        base_url = (
            f"https://github.com/apps/{settings.GITHUB_APP_NAME}/installations/new/permissions"
        )
        query_params = urlencode(
            {
                "suggested_target_id": self.target_id,
                "repository_ids[]": self.project.remote_repository.remote_id,
            }
        )
        return f"{base_url}?{query_params}"

    @property
    def can_be_migrated(self):
        """
        Check if the project can be migrated.

        The project can be migrated if the user is an admin on the repository and the GitHub App is installed.
        """
        return self.is_admin and self.has_installation


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    webhook_removed: bool
    ssh_key_removed: bool


class MigrationError(Exception):
    """Error raised when a migration operation fails."""

    pass


def get_installation_target_groups_for_user(user) -> list[InstallationTargetGroup]:
    """Get all targets (accounts and organizations) that the user needs to install the GitHub App on."""
    # Since we don't save the ID of the owner of each repository, we group all repositories
    # that we aren't able to identify the owner into the user's account.
    # GitHub will ignore the repositories that the user doesn't own.
    default_target_account = _get_default_github_account_target(user)

    targets = {}
    for project, has_intallation, _ in _get_projects_missing_migration(user):
        remote_repository = project.remote_repository
        target_account = _get_github_account_target(remote_repository) or default_target_account
        if target_account.id not in targets:
            targets[target_account.id] = InstallationTargetGroup(
                target=target_account,
                repository_ids=set(),
            )
        if not has_intallation:
            targets[target_account.id].repository_ids.add(int(remote_repository.remote_id))

    # Include accounts that have already migrated projects,
    # so they are shown as "Installed" in the UI.
    for project in get_migrated_projects(user):
        remote_repository = project.remote_repository
        target_account = _get_github_account_target(remote_repository) or default_target_account
        if target_account.id not in targets:
            targets[target_account.id] = InstallationTargetGroup(
                target=target_account,
                repository_ids=set(),
            )

    return list(targets.values())


def _get_default_github_account_target(user) -> GitHubAccountTarget:
    """
    Get the GitHub account from the user.

    We first try to get the account from our old GitHub OAuth App,
    and fallback to the new GitHub App if we can't find it.

    .. note::

       There are some users that have more than one GH account connected.
       They will need to migrate each account at a time.
    """
    # This needs to support multiple accounts....
    account = user.socialaccount_set.filter(provider=GitHubProvider.id).first()
    if not account:
        account = user.socialaccount_set.filter(provider=GitHubAppProvider.id).first()

    return GitHubAccountTarget(
        # We shouldn't have users without a login, but just in case.
        login=account.extra_data.get("login", "ghost"),
        id=int(account.uid),
        type=GitHubAccountType.USER,
        avatar_url=account.get_avatar_url(),
        profile_url=account.get_profile_url(),
    )


def _get_github_account_target(remote_repository) -> GitHubAccountTarget | None:
    """
    Get the GitHub account target for a repository.

    This will return the account that owns the repository, if we can identify it.
    For repositories owned by organizations, we return the organization account,
    for repositories owned by users, we try to guess the account based on the repository owner
    (as we don't save the owner ID in the remote repository object).
    """
    remote_organization = remote_repository.organization
    if remote_organization:
        return GitHubAccountTarget(
            login=remote_organization.slug,
            id=int(remote_organization.remote_id),
            type=GitHubAccountType.ORGANIZATION,
            avatar_url=remote_organization.avatar_url,
            profile_url=remote_organization.url,
        )
    login = remote_repository.full_name.split("/", 1)[0]
    account = SocialAccount.objects.filter(
        provider__in=[GitHubProvider.id, GitHubAppProvider.id], extra_data__login=login
    ).first()
    if account:
        return GitHubAccountTarget(
            login=login,
            id=int(account.uid),
            type=GitHubAccountType.USER,
            avatar_url=account.get_avatar_url(),
            profile_url=account.get_profile_url(),
        )
    return None


def _get_projects_missing_migration(user) -> Iterator[tuple[Project, bool, bool]]:
    """
    Get all projects where the user has access that are still connected to the old GitHub OAuth App.

    Returns an iterator with the project, a boolean indicating if the GitHub App is installed on the repository,
    and a boolean indicating if the user has admin permissions on the repository.
    """
    projects = (
        AdminPermission.projects(user, admin=True)
        .filter(remote_repository__vcs_provider=GITHUB)
        .select_related(
            "remote_repository",
            "remote_repository__organization",
        )
    )
    for project in projects:
        remote_repository = project.remote_repository
        has_installation = RemoteRepository.objects.filter(
            remote_id=remote_repository.remote_id,
            vcs_provider=GITHUB_APP,
            github_app_installation__isnull=False,
        ).exists()
        is_admin = (
            RemoteRepository.objects.for_project_linking(user)
            .filter(
                remote_id=project.remote_repository.remote_id,
                vcs_provider=GITHUB_APP,
                github_app_installation__isnull=False,
            )
            .exists()
        )
        yield project, has_installation, is_admin


def get_migrated_projects(user):
    """
    Get all projects from the user that are already migrated to the GitHub App.

    This is basically all projects that are connected to a remote repository from the GitHub App.
    """
    return (
        AdminPermission.projects(user, admin=True)
        .filter(remote_repository__vcs_provider=GITHUB_APP)
        .select_related(
            "remote_repository",
        )
    )


def get_valid_projects_missing_migration(user) -> Iterator[Project]:
    """
    Get all projects that the user can migrate to the GitHub App.

    This includes all projects that are connected to the old GitHub OAuth App,
    where the user has admin permissions and the GitHub App is installed.
    """
    for project, has_installation, is_admin in _get_projects_missing_migration(user):
        if has_installation and is_admin:
            yield project


def get_migration_targets(user) -> list[MigrationTarget]:
    """
    Get all projects that the user needs to migrate to the GitHub App.

    This includes all projects that are connected to the old GitHub OAuth App,
    doesn't matter if the user has admin permissions or the GitHub App is installed.
    """
    targets = []
    default_target_account = _get_default_github_account_target(user)
    for project, has_installation, is_admin in _get_projects_missing_migration(user):
        remote_repository = project.remote_repository
        target_account = _get_github_account_target(remote_repository) or default_target_account
        targets.append(
            MigrationTarget(
                project=project,
                has_installation=has_installation,
                is_admin=is_admin,
                target_id=target_account.id,
            )
        )
    return targets


def has_projects_pending_migration(user) -> bool:
    """
    Check if the user has any projects pending migration to the GitHub App.

    This includes all projects that are connected to the old GitHub OAuth App,
    where the user has admin permissions and the GitHub App is installed.
    """
    return any(_get_projects_missing_migration(user))


def get_old_app_link() -> str:
    """
    Get the link to the old GitHub OAuth App settings page.

    Useful so users can revoke the old app.
    """
    client_id = settings.SOCIALACCOUNT_PROVIDERS["github"]["APPS"][0]["client_id"]
    return f"https://github.com/settings/connections/applications/{client_id}"


def migrate_project_to_github_app(project, user) -> MigrationResult:
    """
    Migrate a project to the new GitHub App.

    This will remove the webhook and SSH key from the old GitHub OAuth App and
    connect the project to the new GitHub App.

    Returns a MigrationResult with the status of the migration.
    Raises a MigrationError if the project can't be migrated,
    this should never happen as we don't allow migrating projects
    that can't be migrated from the UI.
    """
    # No remote repository, nothing to migrate.
    if not project.remote_repository:
        raise MigrationError("Project isn't connected to a repository")

    service_class = project.get_git_service_class()

    # Already migrated, nothing to do.
    if service_class == GitHubAppService:
        return MigrationResult(webhook_removed=True, ssh_key_removed=True)

    # Not a GitHub project, nothing to migrate.
    if service_class != GitHubService:
        raise MigrationError("Project isn't connected to a GitHub repository")

    new_remote_repository = RemoteRepository.objects.filter(
        remote_id=project.remote_repository.remote_id,
        vcs_provider=GITHUB_APP,
        github_app_installation__isnull=False,
    ).first()

    if not new_remote_repository:
        raise MigrationError("You need to install the GitHub App on the repository")

    new_remote_repository = (
        RemoteRepository.objects.for_project_linking(user)
        .filter(
            remote_id=project.remote_repository.remote_id,
            vcs_provider=GITHUB_APP,
            github_app_installation__isnull=False,
        )
        .first()
    )
    if not new_remote_repository:
        raise MigrationError("You must have admin permissions on the repository to migrate it")

    webhook_removed = False
    ssh_key_removed = False
    for service in service_class.for_project(project):
        if not webhook_removed and service.remove_webhook(project):
            webhook_removed = True

        if not ssh_key_removed and service.remove_ssh_key(project):
            ssh_key_removed = True

    project.integrations.filter(integration_type=Integration.GITHUB_WEBHOOK).delete()
    project.remote_repository = new_remote_repository
    project.save()
    return MigrationResult(
        webhook_removed=webhook_removed,
        ssh_key_removed=ssh_key_removed,
    )
