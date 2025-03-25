"""This module contains the logic to help users migrate from the GitHub OAuth App to the GitHub App."""

from dataclasses import dataclass

from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings

from readthedocs.core.permissions import AdminPermission
from readthedocs.integrations.models import Integration
from readthedocs.oauth.constants import GITHUB
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAccountType
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.services import GitHubAppService
from readthedocs.oauth.services import GitHubService
from readthedocs.projects.models import Project


@dataclass
class InstallationTargetGroup:
    """Group of repositories that should be installed in the same target (user or organization)."""

    target_id: int
    target_type: GitHubAccountType
    target_name: str
    repository_ids: set[int]

    @property
    def link(self):
        """
        Create a link to install the GitHub App on the target with the required repositories pre-selected.

        See https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/migrating-oauth-apps-to-github-apps#prompt-users-to-install-your-github-app.
        """
        repository_ids = []
        for repository_id in self.repository_ids:
            repository_ids.append(f"&repository_ids[]={repository_id}")
        repository_ids = "".join(repository_ids)

        base_url = (
            f"https://github.com/apps/{settings.GITHUB_APP_NAME}/installations/new/permissions"
        )
        return f"{base_url}?suggested_target_id={self.target_id}{repository_ids}"

    @property
    def installed(self):
        """
        Check if the app was already installed on the target.

        If we don't have any repositories left to install, the app was already installed,
        or we don't have any repositories to install the app on.
        """
        return not bool(self.repository_ids)


def get_installation_target_groups_for_user(user) -> list[InstallationTargetGroup]:
    """Get all targets (accounts and organizations) that the user needs to install the GitHub App on."""
    targets = {}
    account = user.socialaccount_set.filter(provider=GitHubProvider.id).first()

    # Since we don't save the ID of the owner of each repository, we group all repositories
    # that don't have an organization under the user account,
    # GitHub will ignore the repositories that the user doesn't own.
    targets[int(account.uid)] = InstallationTargetGroup(
        target_id=int(account.uid),
        target_name=account.extra_data.get("login", "unknown"),
        target_type=GitHubAccountType.USER,
        repository_ids=set(),
    )

    for project, has_intallation, _ in _get_projects_missing_migration(user):
        remote_repository = project.remote_repository
        if remote_repository.organization:
            target_id = int(remote_repository.organization.remote_id)
            if target_id not in targets:
                targets[target_id] = InstallationTargetGroup(
                    target_id=target_id,
                    target_name=remote_repository.organization.slug,
                    target_type=GitHubAccountType.ORGANIZATION,
                    repository_ids=set(),
                )
        else:
            target_id = int(account.uid)

        if not has_intallation:
            targets[target_id].repository_ids.add(int(remote_repository.remote_id))

    return list(targets.values())


def _get_projects_missing_migration(user):
    """
    Get all projects where the user has admin permissions that are still connected to the old GitHub OAuth App.

    Returns a generator with the project, a boolean indicating if the GitHub App is installed on the repository,
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


def get_valid_projects_missing_migration(user):
    for project, has_installation, is_admin in _get_projects_missing_migration(user):
        if has_installation and is_admin:
            yield project


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
        return f"{base_url}?suggested_target_id={self.target_id}&repository_ids[]={self.project.remote_repository.remote_id}"

    @property
    def can_be_migrated(self):
        """
        Check if the project can be migrated.

        The project can be migrated if the user is an admin on the repository and the GitHub App is installed.
        """
        return self.is_admin and self.has_installation


def get_migration_targets(user):
    """Get all projects that the user needs to migrate to the GitHub App."""
    targets = []
    # NOTE: there are some users that have more than one GH account connected.
    # They will need to migrate each account at a time.
    gh_account = user.socialaccount_set.filter(provider=GITHUB).first()
    if not gh_account:
        return targets

    for project, has_installation, is_admin in _get_projects_missing_migration(user):
        remote_repository = project.remote_repository
        if remote_repository.organization:
            target_id = int(remote_repository.organization.remote_id)
        else:
            target_id = int(gh_account.uid)
        targets.append(
            MigrationTarget(
                project=project,
                has_installation=has_installation,
                is_admin=is_admin,
                target_id=target_id,
            )
        )
    return targets


def get_old_app_link():
    """
    Get the link to the old GitHub OAuth App settings page.

    Useful so users can revoke the old app.
    """
    client_id = settings.SOCIALACCOUNT_PROVIDERS["github"]["APPS"][0]["client_id"]
    return f"https://github.com/settings/connections/applications/{client_id}"


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    webhook_removed: bool
    ssh_key_removed: bool


class MigrationError(Exception):
    pass


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
