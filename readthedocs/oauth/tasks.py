"""Tasks for OAuth services."""

import datetime
from functools import cached_property

import structlog
from django.contrib.auth.models import User
from django.db.models.functions import ExtractIsoWeekDay
from django.urls import reverse
from django.utils import timezone

from readthedocs.api.v2.views.integrations import ExternalVersionData
from readthedocs.builds.utils import memcache_lock
from readthedocs.core.utils.tasks import PublicTask
from readthedocs.core.utils.tasks import user_id_matches_or_superuser
from readthedocs.core.views.hooks import VersionInfo
from readthedocs.core.views.hooks import build_external_version
from readthedocs.core.views.hooks import build_versions_from_names
from readthedocs.core.views.hooks import close_external_version
from readthedocs.core.views.hooks import get_or_create_external_version
from readthedocs.core.views.hooks import trigger_sync_versions
from readthedocs.notifications.models import Notification
from readthedocs.oauth.clients import get_gh_app_client
from readthedocs.oauth.constants import GITHUB_APP
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.oauth.models import RemoteRepository
from readthedocs.oauth.notifications import MESSAGE_OAUTH_WEBHOOK_INVALID
from readthedocs.oauth.notifications import MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT
from readthedocs.oauth.notifications import MESSAGE_OAUTH_WEBHOOK_NO_PERMISSIONS
from readthedocs.oauth.services import GitHubAppService
from readthedocs.oauth.services import registry
from readthedocs.oauth.services.base import SyncServiceError
from readthedocs.oauth.utils import SERVICE_MAP
from readthedocs.projects.models import Project
from readthedocs.sso.models import SSOIntegration
from readthedocs.vcs_support.backends.git import parse_version_from_ref
from readthedocs.worker import app


log = structlog.get_logger(__name__)


@PublicTask.permission_check(user_id_matches_or_superuser)
@app.task(
    queue="web",
    base=PublicTask,
    # We have experienced timeout problems on users having a lot of
    # repositories to sync. This is usually due to users belonging to big
    # organizations (e.g. conda-forge).
    time_limit=900,
    soft_time_limit=600,
)
def sync_remote_repositories(user_id, skip_githubapp=False):
    user = User.objects.filter(pk=user_id).first()
    if not user:
        return

    failed_services = set()
    for service_cls in registry:
        if skip_githubapp and service_cls == GitHubAppService:
            continue

        try:
            service_cls.sync_user_access(user)
        except SyncServiceError:
            failed_services.add(service_cls.allauth_provider.name)

    if failed_services:
        raise SyncServiceError(
            SyncServiceError.INVALID_OR_REVOKED_ACCESS_TOKEN.format(
                provider=", ".join(failed_services)
            )
        )


@app.task(
    queue="web",
    # This is a long running task, since it syncs all repositories one by one.
    time_limit=60 * 60 * 3,  # 3h
    soft_time_limit=(60 * 60 * 3) - 5 * 60,  # 2h 55m
)
def sync_remote_repositories_from_sso_organizations():
    """
    Re-sync all remote repositories from organizations with SSO enabled.

    This is useful, so all the remote repositories are up to date with the
    latest permissions from their providers.

    We ignore repositories from GitHub App installations, since they are kept
    up to date via webhooks. For all the other services, we need to sync the
    repository for each user that has access to it, since we need to check for
    their permissions individually.
    """
    repositories = (
        RemoteRepository.objects.filter(
            projects__organizations__ssointegration__provider=SSOIntegration.PROVIDER_ALLAUTH,
        )
        .exclude(vcs_provider=GITHUB_APP)
        .distinct()
    )
    for repository in repositories.iterator():
        service_class = repository.get_service_class()
        relations = repository.remote_repository_relations.select_related("user", "account")
        for relation in relations.iterator():
            service = service_class(user=relation.user, account=relation.account)
            try:
                service.update_repository(repository)
            except Exception:
                log.info(
                    "There was a problem updating repository for user.",
                    user_username=relation.user.username,
                    account_uid=relation.account.uid,
                    repository_remote_id=repository.remote_id,
                    repository_name=repository.full_name,
                )


@app.task(
    queue="web",
    time_limit=60 * 60 * 3,  # 3h
    soft_time_limit=(60 * 60 * 3) - 5 * 60,  # 2h 55m
    bind=True,
)
def sync_active_users_remote_repositories(self):
    """
    Sync ``RemoteRepository`` for active users.

    We consider active users those that logged in at least once in the last 45 days.

    This task is thought to be executed daily. It checks the weekday of the
    last login of the user with today's weekday. If they match, the re-sync is
    triggered. This logic guarantees us the re-sync to be done once a week per user.

    Note this is a long running task syncronizhing all the users in the same Celery process,
    and it will require a pretty high ``time_limit`` and ``soft_time_limit``.
    """
    # This task is expensive, and we run it daily.
    # We have had issues with it being triggered multiple times per day,
    # so we use a lock (12 hours) to avoid that.
    lock_id = "{0}-lock".format(self.name)
    with memcache_lock(lock_id, 60 * 60 * 12, self.app.oid) as acquired:
        if not acquired:
            log.exception("Task has already been run recently, exiting.")
            return

        today_weekday = timezone.now().isoweekday()
        days_ago = timezone.now() - datetime.timedelta(days=45)
        users = User.objects.annotate(weekday=ExtractIsoWeekDay("last_login")).filter(
            last_login__gt=days_ago,
            socialaccount__isnull=False,
            weekday=today_weekday,
        )

        users_count = users.count()
        structlog.contextvars.bind_contextvars(total_users=users_count)
        log.info("Triggering re-sync of RemoteRepository for active users.")

        for i, user in enumerate(users.iterator()):
            structlog.contextvars.bind_contextvars(
                user_username=user.username,
                progress=f"{i}/{users_count}",
            )

            # Log an update every 50 users
            if i % 50 == 0:
                log.info("Progress on re-syncing RemoteRepository for active users.")

            try:
                # NOTE: sync all the users/repositories in the same Celery process.
                # Do not trigger a new task per user.
                # NOTE: We skip the GitHub App, since all the repositories
                # and permissions are kept up to date via webhooks.
                # Triggering a sync per-user, will re-sync the same installation
                # multiple times.
                sync_remote_repositories(
                    user.pk,
                    skip_githubapp=True,
                )
            except Exception:
                log.exception("There was a problem re-syncing RemoteRepository.")


# TODO: remove user_pk from the signature on the next release.
@app.task(queue="web")
def attach_webhook(project_pk, user_pk=None, integration=None, **kwargs):
    """
    Add post-commit hook on project import.

    This is a brute force approach to add a webhook to a repository. We try
    all accounts until we set up a webhook. This should remain around for legacy
    connections -- that is, projects that do not have a remote repository them
    and were not set up with a VCS provider.

    :param project_pk: Project primary key
    :param integration: Integration instance. If used, this function should
     be called directly, not as a task.
    """
    project = Project.objects.filter(pk=project_pk).first()
    if not project:
        return False

    if integration:
        service_class = SERVICE_MAP.get(integration.integration_type)
    else:
        # Get the service class for the project e.g: GitHubService.
        # We fallback to guess the service from the repo,
        # in the future we should only consider projects that have a remote repository.
        service_class = project.get_git_service_class(fallback_to_clone_url=True)

    if not service_class:
        Notification.objects.add(
            message_id=MESSAGE_OAUTH_WEBHOOK_INVALID,
            attached_to=project,
            dismissable=True,
            format_values={
                "url_integrations": reverse(
                    "projects_integrations",
                    args=[project.slug],
                ),
            },
        )
        return False

    services = list(service_class.for_project(project))
    if not services:
        Notification.objects.add(
            message_id=MESSAGE_OAUTH_WEBHOOK_NO_ACCOUNT,
            dismissable=True,
            attached_to=project,
            format_values={
                "provider_name": service_class.allauth_provider.name,
                "url_connect_account": reverse(
                    "projects_integrations",
                    args=[project.slug],
                ),
            },
        )
        return False

    for service in services:
        success = service.setup_webhook(project, integration=integration)
        if success:
            project.has_valid_webhook = True
            project.save()
            return True

    Notification.objects.add(
        message_id=MESSAGE_OAUTH_WEBHOOK_NO_PERMISSIONS,
        dismissable=True,
        attached_to=project,
        format_values={
            "provider_name": service_class.allauth_provider.name,
            "url_docs_webhook": "https://docs.readthedocs.io/page/webhooks.html",
        },
    )
    return False


class GitHubAppWebhookHandler:
    """
    Handle GitHub App webhooks.

    All event handlers try to create the installation object if it doesn't exist in our database,
    except for events related to the installation being deleted or suspended.
    This guarantees that our application can easily recover if we missed an event
    in case our application or GitHub were down.
    """

    def __init__(self, data: dict, event: str):
        self.data = data
        self.event = event
        self.event_handlers = {
            "installation": self._handle_installation_event,
            "installation_repositories": self._handle_installation_repositories_event,
            "installation_target": self._handle_installation_target_event,
            "push": self._handle_push_event,
            "pull_request": self._handle_pull_request_event,
            "repository": self._handle_repository_event,
            "organization": self._handle_organization_event,
            "member": self._handle_member_event,
            "github_app_authorization": self._handle_github_app_authorization_event,
        }

    @cached_property
    def gh_app_client(self):
        return get_gh_app_client()

    def handle(self):
        # Most of the events have an installation object and action.
        installation_id = self.data.get("installation", {}).get("id", "unknown")
        action = self.data.get("action", "unknown")
        structlog.contextvars.bind_contextvars(
            installation_id=installation_id,
            action=action,
            event=self.event,
        )
        if self.event not in self.event_handlers:
            log.debug("Unsupported event")
            raise ValueError(f"Unsupported event: {self.event}")

        log.info("Handling event")
        self.event_handlers[self.event]()

    def _handle_installation_event(self):
        """
        Handle the installation event.

        Triggered when a user installs or uninstalls the GitHub App under an account (user or organization).
        We create the installation object and sync the repositories, or delete the installation accordingly.

        Payload example:

        .. code-block:: json

           {
             "action": "created",
             "installation": {
                 "id": 1234,
                 "client_id": "12345",
                 "account": {
                     "login": "user",
                     "id": 12345,
                     "type": "User"
                 },
                 "repository_selection": "selected",
                 "html_url": "https://github.com/settings/installations/1234",
                 "app_id": 12345,
                 "app_slug": "app-slug",
                 "target_id": 12345,
                 "target_type": "User",
                 "permissions": {
                     "contents": "read",
                     "metadata": "read",
                     "pull_requests": "write",
                     "statuses": "write"
                 },
                 "events": [
                     "create",
                     "delete",
                     "public",
                     "pull_request",
                     "push"
                 ],
                 "created_at": "2025-01-29T12:04:11.000-05:00",
                 "updated_at": "2025-01-29T12:04:12.000-05:00",
                 "single_file_name": null,
                 "has_multiple_single_files": false,
                 "single_file_paths": [],
                 "suspended_by": null,
                 "suspended_at": null
             },
             "repositories": [
                 {
                     "id": 770738492,
                     "name": "test-public",
                     "full_name": "user/test-public",
                     "private": false
                 },
                 {
                     "id": 917825438,
                     "name": "test-private",
                     "full_name": "user/test-private",
                     "private": true
                 }
             ],
             "requester": null,
             "sender": {
                 "login": "user",
                 "id": 1234,
                 "type": "User"
              }
           }

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation.
        """
        action = self.data["action"]
        gh_installation = self.data["installation"]
        installation_id = gh_installation["id"]

        if action in ["created", "unsuspended"]:
            installation, created = self._get_or_create_installation()
            # If the installation was just created, we already synced the repositories.
            if created:
                return
            installation.service.sync()

        if action in ["deleted", "suspended"]:
            # NOTE: When an installation is deleted/suspended, it doesn't trigger an installation_repositories event.
            # So we need to call the delete method explicitly here, so we delete its repositories.
            installation = GitHubAppInstallation.objects.filter(
                installation_id=installation_id
            ).first()
            if installation:
                installation.delete()
                log.info("Installation deleted")
            else:
                log.info("Installation not found")
            return

        # Ignore other actions:
        # - new_permissions_accepted: We don't need to do anything here for now.
        return

    def _handle_installation_repositories_event(self):
        """
        Handle the installation_repositories event.

        Triggered when a repository is added or removed from an installation.

        If the installation had access to a repository, and the repository is deleted,
        this event will be triggered.

        When a repository is deleted, we delete its remote repository object,
        but only if it's not linked to any project.

        Payload example:

        .. code-block:: json
           {
             "action": "added",
             "installation": {
               "id": 1234,
               "client_id": "1234",
               "account": {
                 "login": "user",
                 "id": 12345,
                 "type": "User"
               },
               "repository_selection": "selected",
               "html_url": "https://github.com/settings/installations/60240360",
               "app_id": 12345,
               "app_slug": "app-slug",
               "target_id": 12345,
               "target_type": "User",
               "permissions": {
                 "contents": "read",
                 "metadata": "read",
                 "pull_requests": "write",
                 "statuses": "write"
               },
               "events": ["create", "delete", "public", "pull_request", "push"],
               "created_at": "2025-01-29T12:04:11.000-05:00",
               "updated_at": "2025-01-29T16:05:45.000-05:00",
               "single_file_name": null,
               "has_multiple_single_files": false,
               "single_file_paths": [],
               "suspended_by": null,
               "suspended_at": null
             },
             "repository_selection": "selected",
             "repositories_added": [
               {
                 "id": 258664698,
                 "name": "test-public",
                 "full_name": "user/test-public",
                 "private": false
               }
             ],
             "repositories_removed": [],
             "requester": null,
             "sender": {
               "login": "user",
               "id": 4975310,
               "type": "User"
             }
           }

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation_repositories.
        """
        action = self.data["action"]
        installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        if action == "added":
            if self.data["repository_selection"] == "all":
                installation.service.sync()
            else:
                installation.service.update_or_create_repositories(
                    [repo["id"] for repo in self.data["repositories_added"]]
                )
            return

        if action == "removed":
            installation.delete_repositories(
                [repo["id"] for repo in self.data["repositories_removed"]]
            )
            return

        # NOTE: this should never happen.
        raise ValueError(f"Unsupported action: {action}")

    def _handle_installation_target_event(self):
        """
        Handle the installation_target event.

        Triggered when the target of an installation changes,
        like when the user or organization changes its username/slug.

        .. note::

           Looks like this is only triggered when a username is changed,
           when an organization is renamed, it doesn't trigger this event
           (maybe a bug?).

        When this happens, we re-sync all the repositories, so they use the new name.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#installation_target.
        """
        installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        installation.service.sync()

    def _handle_repository_event(self):
        """
        Handle the repository event.

        Triggered when a repository is created, deleted, or updated.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#repository.
        """
        action = self.data["action"]

        installation, created = self._get_or_create_installation()

        # If the installation was just created, we already synced the repositories.
        if created:
            return

        if action in ("edited", "privatized", "publicized", "renamed", "transferred"):
            installation.service.update_or_create_repositories([self.data["repository"]["id"]])
            return

        # Ignore other actions:
        # - created: If the user granted access to all repositories,
        #   GH will trigger an installation_repositories event.
        # - deleted: If the repository was linked to an installation,
        #   GH will be trigger an installation_repositories event.
        # - archived/unarchived: We don't do anything with archived repositories.
        return

    def _handle_push_event(self):
        """
        Handle the push event.

        Triggered when a commit is pushed (including a new branch or tag is created),
        when a branch or tag is deleted, or when a repository is created from a template.

        If a new branch or tag is created, we trigger a sync of the versions,
        if the version already exists, we build it if it's active.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#push.
        """
        created = self.data.get("created", False)
        deleted = self.data.get("deleted", False)
        if created or deleted:
            for project in self._get_projects():
                trigger_sync_versions(project)
            return

        # If this is a push to an existing branch or tag,
        # we need to build the version if active.
        version_name, version_type = parse_version_from_ref(self.data["ref"])
        for project in self._get_projects():
            build_versions_from_names(project, [VersionInfo(name=version_name, type=version_type)])

    def _handle_pull_request_event(self):
        """
        Handle the pull_request event.

        Triggered when there is activity on a pull request.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request.
        """
        action = self.data["action"]

        pr = self.data["pull_request"]
        external_version_data = ExternalVersionData(
            id=str(pr["number"]),
            commit=pr["head"]["sha"],
            source_branch=pr["head"]["ref"],
            base_branch=pr["base"]["ref"],
        )

        if action in ("opened", "reopened", "synchronize"):
            for project in self._get_projects().filter(external_builds_enabled=True):
                external_version = get_or_create_external_version(
                    project=project,
                    version_data=external_version_data,
                )
                build_external_version(project, external_version)
            return

        if action == "closed":
            # Queue the external version for deletion.
            for project in self._get_projects():
                close_external_version(
                    project=project,
                    version_data=external_version_data,
                )
            return

        # We don't care about the other actions.
        return

    def _handle_organization_event(self):
        """
        Handle the organization event.

        Triggered when an member is added or removed from an organization,
        or when the organization is renamed or deleted.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#organization.
        """
        action = self.data["action"]

        installation, created = self._get_or_create_installation()

        # If the installation was just created, we already synced the repositories and organization.
        if created:
            return

        # We need to do a full sync of the repositories if members were added or removed,
        # this is since we don't know to which repositories the members have access.
        # GH doesn't send a member event for this.
        if action in ("member_added", "member_removed"):
            installation.service.sync()
            return

        # NOTE: installation_target should handle this instead?
        # But I wasn't able to trigger neither of those events when renaming an organization.
        # Maybe a bug?
        # If the organization is renamed, we need to sync the repositories, so they use the new name.
        if action == "renamed":
            installation.service.sync()
            return

        if action == "deleted":
            # Delete the organization only if it's not linked to any project.
            # GH sends a repository and installation_repositories events for each repository
            # when the organization is deleted.
            # I didn't see GH send the deleted action for the organization event...
            # But handle it just in case.
            installation.delete_organization(self.data["organization"]["id"])
            return

        # Ignore other actions:
        # - member_invited: We don't do anything with invited members.
        return

    def _handle_member_event(self):
        """
        Handle the member event.

        Triggered when a user is added or removed from a repository.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#member.
        """
        action = self.data["action"]

        installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        if action in ("added", "edited", "removed"):
            # Sync collaborators
            installation.service.update_or_create_repositories([self.data["repository"]["id"]])
            return

        # NOTE: this should never happen.
        raise ValueError(f"Unsupported action: {action}")

    def _handle_github_app_authorization_event(self):
        """
        Handle the github_app_authorization event.

        Triggered when a user revokes the authorization of a GitHub App ("log in with GitHub" will no longer work).

        .. note::

           Revoking the authorization of a GitHub App does not uninstall the GitHub App,
           it only revokes the OAuth2 token.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#github_app_authorization.
        """
        # A GitHub App receives this webhook by default and cannot unsubscribe from this event.
        # We don't need to do anything here for now.

    def _get_projects(self):
        """
        Get all projects linked to the repository that triggered the event.

        .. note::

           This should only be used for events that have a repository object.
        """
        remote_repository = self._get_remote_repository()
        if not remote_repository:
            return Project.objects.none()
        return remote_repository.projects.all()

    def _get_remote_repository(self):
        """
        Get the remote repository from the request data.

        If the repository doesn't exist, return None.

        .. note::

           This should only be used for events that have a repository object.
        """
        remote_id = self.data["repository"]["id"]
        installation, _ = self._get_or_create_installation()
        return installation.repositories.filter(remote_id=str(remote_id)).first()

    def _get_or_create_installation(self, sync_repositories_on_create: bool = True):
        """
        Get or create the GitHub App installation.

        If the installation didn't exist, and `sync_repositories_on_create` is True,
        we sync the repositories.
        """
        data = self.data.copy()
        # All webhook payloads should have an installation object.
        gh_installation = self.data["installation"]
        installation_id = gh_installation["id"]

        # These fields are not always present in all payloads.
        target_id = gh_installation.get("target_id")
        target_type = gh_installation.get("target_type")
        # If they aren't present, fetch them from the API,
        # so we can create the installation object if needed.
        if not target_id or not target_type:
            log.debug("Incomplete installation object, fetching from the API")
            gh_installation = self.gh_app_client.get_app_installation(installation_id)
            target_id = gh_installation.target_id
            target_type = gh_installation.target_type
            data["installation"] = gh_installation.raw_data

        (
            installation,
            created,
        ) = GitHubAppInstallation.objects.get_or_create_installation(
            installation_id=installation_id,
            target_id=target_id,
            target_type=target_type,
            extra_data=data,
        )
        if created and sync_repositories_on_create:
            installation.service.sync()
        return installation, created


@app.task(queue="web")
def handle_github_app_webhook(data: dict, event: str, event_id: str = "unknown"):
    """
    Handle GitHub App webhooks asynchronously.

    :param data: The webhook payload data.
    :param event: The event type of the webhook.
    """
    structlog.contextvars.bind_contextvars(
        event=event,
        event_id=event_id,
    )
    log.info("Handling GitHub App webhook")
    handler = GitHubAppWebhookHandler(data, event)
    handler.handle()
