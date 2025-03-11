import hmac
from functools import cached_property

import structlog
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.views.integrations import GITHUB_EVENT_HEADER
from readthedocs.api.v2.views.integrations import GITHUB_SIGNATURE_HEADER
from readthedocs.api.v2.views.integrations import ExternalVersionData
from readthedocs.api.v2.views.integrations import WebhookMixin
from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import TAG
from readthedocs.core.views.hooks import build_external_version
from readthedocs.core.views.hooks import build_versions_from_names
from readthedocs.core.views.hooks import close_external_version
from readthedocs.core.views.hooks import get_or_create_external_version
from readthedocs.core.views.hooks import trigger_sync_versions
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.oauth.services.githubapp import get_gh_app_client
from readthedocs.projects.models import Project


log = structlog.get_logger(__name__)


class GitHubAppWebhookView(APIView):
    authentication_classes = []

    @cached_property
    def gha_client(self):
        return get_gh_app_client()

    def post(self, request):
        if not self._is_payload_signature_valid():
            log.debug("Invalid webhook signature")
            raise ValidationError("Invalid webhook signature")

        # Most of the events have an installation object and action.
        installation_id = request.data.get("installation", {}).get("id", "unknown")
        action = request.data.get("action", "unknown")
        event = self.request.headers.get(GITHUB_EVENT_HEADER)
        event_handlers = {
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
        log.bind(
            installation_id=installation_id,
            action=action,
            event=event,
        )
        if event in event_handlers:
            log.debug("Handling event")
            event_handlers[event]()
            return Response(status=200)

        log.debug("Unsupported event")
        raise ValidationError(f"Unsupported event: {event}")

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
        data = self.request.data
        action = data["action"]
        gh_installation = data["installation"]
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
        data = self.request.data
        action = data["action"]
        installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        if action == "added":
            if data["repository_selection"] == "all":
                installation.service.sync()
            else:
                installation.service.update_or_create_repositories(
                    [repo["id"] for repo in data["repositories_added"]]
                )
            return

        if action == "removed":
            installation.delete_repositories([repo["id"] for repo in data["repositories_removed"]])
            return

        # NOTE: this should never happen.
        raise ValidationError(f"Unsupported action: {action}")

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
        data = self.request.data
        action = data["action"]

        installation, created = self._get_or_create_installation()

        # If the installation was just created, we already synced the repositories.
        if created:
            return

        if action in ("edited", "privatized", "publicized", "renamed", "transferred"):
            installation.service.update_or_create_repositories([data["repository"]["id"]])
            return

        # Ignore other actions:
        # - created: If the user granted access to all repositories,
        #   GH will trigger an installation_repositories event.
        # - deleted: If the repository was linked to an installation,
        #   GH will be trigger an installation_repositories event.
        # - archived/unarchived: We don't do anything with archived repositories.

    def _handle_push_event(self):
        """
        Handle the push event.

        Triggered when a commit is pushed (including a new branch or tag is created),
        when a branch or tag is deleted, or when a repository is created from a template.

        If a new branch or tag is created, we trigger a sync of the versions,
        if the version already exists, we build it if it's active.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#push.
        """
        data = self.request.data
        created = data.get("created", False)
        deleted = data.get("deleted", False)
        if created or deleted:
            for project in self._get_projects():
                trigger_sync_versions(project)
            return

        # If this is a push to an existing branch or tag,
        # we need to build the version if active.
        version_name, version_type = self._parse_version_from_ref(data["ref"])
        for project in self._get_projects():
            build_versions_from_names(project, [(version_name, version_type)])

    def _parse_version_from_ref(self, ref: str):
        """
        Parse the version name and type from a GitHub ref.

        The ref can be a branch or a tag.

        :param ref: The ref to parse (e.g. refs/heads/main, refs/tags/v1.0.0).
        :returns: A tuple with the version name and type.
        """
        heads_prefix = "refs/heads/"
        tags_prefix = "refs/tags/"
        if ref.startswith(heads_prefix):
            return ref.removeprefix(heads_prefix), BRANCH
        if ref.startswith(tags_prefix):
            return ref.removeprefix(tags_prefix), TAG

        # NOTE: this should never happen.
        raise ValidationError(f"Invalid ref: {ref}")

    def _handle_pull_request_event(self):
        """
        Handle the pull_request event.

        Triggered when there is activity on a pull request.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request.
        """
        data = self.request.data
        action = data["action"]

        pr = data["pull_request"]
        external_version_data = ExternalVersionData(
            id=str(pr["number"]),
            commit=pr["head"]["sha"],
            source_branch=pr["head"]["ref"],
            base_branch=pr["base"]["ref"],
        )

        if action in ("opened", "reopened", "synchronize"):
            for project in self._get_projects():
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
        data = self.request.data
        action = data["action"]

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
            installation.delete_organization(data["organization"]["id"])
            return

        # Ignore other actions:
        # - member_invited: We don't do anything with invited members.

    def _handle_member_event(self):
        """
        Handle the member event.

        Triggered when a user is added or removed from a repository.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#member.
        """
        data = self.request.data
        action = data["action"]

        installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        if action in ("added", "edited", "removed"):
            # Sync collaborators
            installation.service.update_or_create_repositories([data["repository"]["id"]])
            return

        # NOTE: this should never happen.
        raise ValidationError(f"Unsupported action: {action}")

    def _handle_github_app_authorization_event(self):
        """
        Revoking the authorization of a GitHub App does not uninstall the GitHub App.
        You should program your GitHub App so that when it receives this webhook,
        it stops calling the API on behalf of the person who revoked the token.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#github_app_authorization.
        """
        # TODO: what to do here?

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
        data = self.request.data
        remote_id = data["repository"]["id"]
        installation, _ = self._get_or_create_installation()
        return installation.repositories.filter(remote_id=str(remote_id)).first()

    def _get_or_create_installation(self, sync_repositories_on_create: bool = True):
        """
        Get or create the GitHub App installation.

        If the installation didn't exist, and `sync_repositories_on_create` is True,
        we sync the repositories.
        """
        data = self.request.data
        # All webhook payloads should have an installation object.
        gh_installation = data["installation"]
        installation_id = gh_installation["id"]

        # These fields are not always present in all payloads.
        target_id = gh_installation.get("target_id")
        target_type = gh_installation.get("target_type")
        # If they aren't present, fetch them from the API,
        # so we can create the installation object if needed.
        if not target_id or not target_type:
            log.debug("Incomplete installation object, fetching from the API")
            gh_installation = self.gha_client.get_app_installation(installation_id)
            target_id = gh_installation.target_id
            target_type = gh_installation.target_type
            data = data.copy()
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

    def _is_payload_signature_valid(self):
        """
        GitHub uses a HMAC hexdigest hash to sign the payload.

        It is sent in the request's header.
        See https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries.
        """
        signature = self.request.headers.get(GITHUB_SIGNATURE_HEADER)
        if not signature:
            return False

        msg = self.request.body.decode()
        secret = settings.GITHUB_APP_WEBHOOK_SECRET
        digest = WebhookMixin.get_digest(secret, msg)
        return hmac.compare_digest(
            f"sha256={digest}".encode(),
            signature.encode(),
        )
