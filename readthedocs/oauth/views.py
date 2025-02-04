import hmac

import structlog
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.views.integrations import (
    GITHUB_EVENT_HEADER,
    GITHUB_SIGNATURE_HEADER,
    ExternalVersionData,
    WebhookMixin,
)
from readthedocs.builds.constants import BRANCH, TAG
from readthedocs.core.views.hooks import (
    build_external_version,
    build_versions_from_names,
    close_external_version,
    get_or_create_external_version,
    trigger_sync_versions,
)
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.projects.models import Project

log = structlog.get_logger(__name__)


class GitHubAppWebhookView(APIView):
    authentication_classes = []

    def post(self, request):
        if not self._is_payload_signature_valid():
            raise ValidationError("Invalid webhook signature")

        event = self.request.headers.get(GITHUB_EVENT_HEADER)

        event_handlers = {
            "installation": self._handle_installation_event,
            "installation_repositories": self._handle_installation_repositories_event,
            # Hmm, don't think we need this one.
            "installation_target": self._handle_installation_target_event,
            # "create": self._handle_create_event,
            # "delete": self._handle_delete_event,
            # TODO: this triggers when a branch or tag is deleted,
            # do we need to handle the delete and create events as well?
            "push": self._handle_push_event,
            "pull_request": self._handle_pull_request_event,
        }
        if event in event_handlers:
            event_handlers[event]()
            return Response(status=200)
        raise ValidationError(f"Unsupported event: {event}")

    def _handle_installation_event(self):
        """
        Handle the installation event.

        Triggered when a user installs or uninstalls the GitHub App under an account (user or organization).

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
        installation = data["installation"]

        if action == "created":
            gha_installation, created = self._get_or_create_installation()
            if not created:
                log.info(
                    "Installation already exists", installation_id=installation["id"]
                )

            return

        if action == "deleted":
            gha_installation = GitHubAppInstallation.objects.filter(
                installation_id=installation["id"]
            ).first()
            if not gha_installation:
                # If we never created the installation, we can ignore the event.
                # Maybe don't raise an error?
                raise ValidationError(f"Installation {installation['id']} not found")
            gha_installation.delete()
            return

        # NOTE: should we handle the suspended/unsuspended/new_permissions_accepted actions?
        raise ValidationError(f"Unsupported action: {action}")

    def _handle_installation_repositories_event(self):
        """
        Handle the installation_repositories event.

        Triggered when a repository is added or removed from an installation.

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
        gha_installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        if action == "added":
            if data["repository_selection"] == "all":
                gha_installation.service.sync_repositories()
            else:
                gha_installation.service.add_repositories(
                    [repo["id"] for repo in data["repositories_added"]]
                )
            return

        if action == "removed":
            gha_installation.service.remove_repositories(
                [repo["id"] for repo in data["repositories_removed"]]
            )
            return

        raise ValidationError(f"Unsupported action: {action}")

    def _handle_installation_target_event(self):
        """
        Handle the installation_target event.

        Triggered when the target of an installation changes,
        like when the user or organization changes its username/slug.
        """

    def _handle_create_event(self):
        """
        Handle the create event.

        Triggered when a branch or tag is created.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#create.
        """
        self._sync_repo_versions()

    def _handle_delete_event(self):
        """
        Handle the delete event.

        Triggered when a branch or tag is deleted.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#delete.
        """
        self._sync_repo_versions()

    def _sync_repo_versions(self):
        for project in self._get_projects():
            trigger_sync_versions(project)

    def _handle_push_event(self):
        """
        Handle the push event.

        Triggered when a commit is pushed, when a commit tag is pushed,
        when a branch is deleted, when a tag is deleted,
        or when a repository is created from a template.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#push.
        """
        data = self.request.data
        created = data.get("created", False)
        deleted = data.get("deleted", False)
        if created or deleted:
            self._sync_repo_versions()
            return

        version_name, version_type = self._parse_version_from_ref(data["ref"])
        for project in self._get_projects():
            build_versions_from_names(project, [(version_name, version_type)])

    def _parse_version_from_ref(self, ref: str):
        """
        Parse the version name and type from a GitHub ref.

        The ref can be a branch or a tag.

        :param ref: The ref to parse.
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
        ExternalVersionData(
            id=str(pr["number"]),
            commit=pr["head"]["sha"],
            source_branch=pr["head"]["ref"],
            base_branch=pr["base"]["ref"],
        )

        if action in ("opened", "reopened", "synchronize"):
            for project in self._get_projects():
                external_version = get_or_create_external_version(
                    project=project,
                    version_data=ExternalVersionData,
                )
                build_external_version(project, external_version)
            return

        if action == "closed":
            # Queue the external version for deletion.
            for project in self._get_projects():
                close_external_version(
                    project=project,
                    version_data=ExternalVersionData,
                )
            return

        # We don't need to handle the other actions.
        return

    def _get_projects(self):
        remote_repository = self._get_remote_repository()
        if not remote_repository:
            return Project.objects.none()
        return remote_repository.projects.all()

    def _get_remote_repository(self):
        """
        Get the remote repository from the request data.

        If the repository doesn't exist, return None.
        """
        data = self.request.data
        remote_id = data["repository"]["id"]
        gha_installation, _ = self._get_or_create_installation()
        return gha_installation.repositories.filter(remote_id=remote_id).first()

    def _get_or_create_installation(self, sync_repositories_on_create: bool = True):
        """
        Get or create the GitHub App installation.

        If the installation didn't exist, and `sync_repositories_on_create` is True,
        we sync the repositories.
        """
        data = self.request.data
        # All webhook payloads should have an installation object.
        installation = data["installation"]
        installation_id = installation["id"]
        target_id = installation["target_id"]
        target_type = installation["target_type"]
        gha_installation, created = GitHubAppInstallation.objects.get_or_create(
            installation_id=installation_id,
            defaults={
                "extra_data": data,
                "target_id": target_id,
                "target_type": target_type,
            },
        )
        # NOTE: An installation can't change its target_id or target_type.
        # This should never happen, unless this assumption is wrong.
        if (
            gha_installation.target_id != target_id
            or gha_installation.target_type != target_type
        ):
            log.exception(
                "Installation target_id or target_type changed",
                installation_id=gha_installation.installation_id,
                target_id=gha_installation.target_id,
                target_type=gha_installation.target_type,
                new_target_id=target_id,
                new_target_type=target_type,
            )
            gha_installation.target_id = target_id
            gha_installation.target_type = target_type
            gha_installation.save()
        if created and sync_repositories_on_create:
            gha_installation.service.sync_repositories()
        return gha_installation, created

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
