from dataclasses import dataclass

from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings

from readthedocs.core.permissions import AdminPermission
from readthedocs.oauth.services import GitHubAppService, GitHubService


def migrate_project_to_github_app(project):
    # No remote repository, nothing to migrate.
    if not project.remote_repository:
        return

    service_class = project.get_git_service_class()

    # Already migrated, nothing to do.
    if service_class == GitHubAppService:
        return

    # Not a GitHub project, nothing to migrate.
    if service_class != GitHubService:
        return


def migrate_user_to_github_app(user):
    pass


class ProjectMigration:

    def __init__(self, project):
        self.project = project

    def grant_permissions_url(self):
        pass


@dataclass
class InstallationTarget:
    target_id: str
    target_type: str
    target_name: str
    repository_ids: set[str]

    @property
    def link(self):
        """
        See https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/migrating-oauth-apps-to-github-apps#prompt-users-to-install-your-github-app.
        """
        repository_ids = []
        for repository_id in self.repository_ids:
            repository_ids.append(f"&repository_ids[]={repository_id}")
        repository_ids = "".join(repository_ids)

        base_url = f"https://github.com/apps/{settings.GITHUB_APP_NAME}/installations/new/permissions"
        return f"{base_url}?suggested_target_id={self.target_id}{repository_ids}"


def get_installation_targets_for_user(user) -> list[InstallationTarget]:
    targets = {}
    user_repositories = set()
    for project in AdminPermission.projects(user, admin=True).select_related(
        "remote_repository", "remote_repository__organization"
    ):
        remote_repository = project.remote_repository
        if not remote_repository:
            continue

        service_class = remote_repository.get_service_class()
        if service_class != GitHubService:
            continue

        if remote_repository.organization:
            organization_id = remote_repository.organization.remote_id
            if organization_id not in targets:
                targets[organization_id] = InstallationTarget(
                    target_id=organization_id,
                    target_name=remote_repository.organization.slug,
                    target_type="organization",
                    repository_ids=set(),
                )
            targets[organization_id].repository_ids.add(remote_repository.remote_id)
        else:
            user_repositories.add(remote_repository)

    # TODO: check how many users have more than one GH account connected.
    # Since we don't know the ID of the owner, we create a link for each connected account.
    # GH will select only the corresponding repositories for each account.
    for account in user.socialaccount_set.filter(provider=GitHubProvider.id):
        targets[account.uid] = InstallationTarget(
            target_id=account.uid,
            target_name=account.extra_data.get("login"),
            target_type="user",
            repository_ids={
                remote_repository.remote_id for remote_repository in user_repositories
            },
        )

    return [target for target in targets.values() if target.repository_ids]


def get_installation_target_for_project(
    account, project
) -> tuple[str, str] | tuple[None, None]:
    remote_repository = project.remote_repository
    if not remote_repository:
        return None, None

    service_class = remote_repository.get_service_class()
    if service_class != GitHubService:
        return None, None

    if remote_repository.organization:
        return remote_repository.organization.remote_id, remote_repository.remote_id

    return account.uid, remote_repository.remote_id


def get_old_app_link():
    client_id = settings.SOCIALACCOUNT_PROVIDERS["github"]["APPS"][0]["client_id"]
    return f"https://github.com/settings/connections/applications/{client_id}"
