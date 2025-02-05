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
from readthedocs.oauth.services.githubapp import GitHubAppClient
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
            "push": self._handle_push_event,
            "pull_request": self._handle_pull_request_event,
            "repository": self._handle_repository_event,
            "organization": self._handle_organization_event,
            "member": self._handle_member_event,
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
        gh_installation = data["installation"]

        if action == "created":
            installation, created = self._get_or_create_installation()
            if not created:
                log.info(
                    "Installation already exists", installation_id=gh_installation["id"]
                )

            return

        if action == "deleted":
            installation = GitHubAppInstallation.objects.filter(
                installation_id=gh_installation["id"]
            ).first()
            if not installation:
                # If we never created the installation, we can ignore the event.
                # Maybe don't raise an error?
                raise ValidationError(f"Installation {gh_installation['id']} not found")
            installation.delete()
            return

        # Ignore other actions:
        # - new_permissions_accepted: We don't need to do anything here for now.
        # - suspended/unsuspended: We don't do anything with suspended installations.
        return

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
        installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        if action == "added":
            if data["repository_selection"] == "all":
                installation.service.sync_repositories()
            else:
                installation.service.update_or_create_repositories(
                    [repo["id"] for repo in data["repositories_added"]]
                )
            return

        if action == "removed":
            installation.service.delete_repositories(
                [repo["id"] for repo in data["repositories_removed"]]
            )
            return

        # NOTE: this should never happen.
        raise ValidationError(f"Unsupported action: {action}")

    def _handle_installation_target_event(self):
        """
        Handle the installation_target event.

        Triggered when the target of an installation changes,
        like when the user or organization changes its username/slug.
        """

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

        if action in ("edited", "privatized", "publicized", "renamed", "trasferred"):
            installation.service.update_or_create_repositories(
                [data["repository"]["id"]]
            )
            return

        # Ignore other actions:
        # - created: If the user granted access to all repositories,
        #   GH will trigger an installation_repositories event.
        # - deleted: If the repository was linked to an installation,
        #   GH will be trigger an installation_repositories event.
        # - archived/unarchived: We don't do anything with archived repositories.

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

        # If this is a push to an existing branch or tag,
        # we need to build the version if active.
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

        # We don't care about the other actions.
        return

    def _handle_organization_event(self):
        """
        Handle the organization event.

        Triggered when an organization is added or removed from a repository.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#organization
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
            installation.service.sync_repositories()
            return

        if action == "renamed":
            # Update organization and its members only.
            # We don't need to sync the repositories.
            installation.service.update_or_create_organization(
                data["organization"]["id"]
            )
            return

        if action == "deleted":
            # Delete the organization only if it's not linked to any project.
            # GH sends a repository and installation_repositories events for each repository
            # when the organization is deleted.
            # I didn't see that GH send the deleted action for the organization event...
            # But handle it just in case.
            installation.service.delete_organization(data["organization"]["id"])
            return

        # Ignore other actions:
        # - member_invited: We don't do anything with invited members.

    def _handle_member_event(self):
        """
        Handle the member event.

        Triggered when a user is added or removed from a repository.

        See https://docs.github.com/en/webhooks/webhook-events-and-payloads#member
        """
        data = self.request.data
        action = data["action"]

        installation, created = self._get_or_create_installation()

        # If we didn't have the installation, all repositories were synced on creation.
        if created:
            return

        if action in ("added", "edited", "removed"):
            # Sync collaborators
            installation.service.update_or_create_repositories(
                [data["repository"]["id"]]
            )

        # NOTE: this should never happen.
        raise ValidationError(f"Unsupported action: {action}")

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
        installation, _ = self._get_or_create_installation()
        return installation.repositories.filter(remote_id=remote_id).first()

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
            gh_installation = GitHubAppClient(installation_id).app_installation
            target_id = gh_installation.target_id
            target_type = gh_installation.target_type
            data = data.copy()
            data["installation"] = gh_installation.raw_data

        installation, created = GitHubAppInstallation.objects.get_or_create(
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
            installation.target_id != target_id
            or installation.target_type != target_type
        ):
            log.exception(
                "Installation target_id or target_type changed",
                installation_id=installation.installation_id,
                target_id=installation.target_id,
                target_type=installation.target_type,
                new_target_id=target_id,
                new_target_type=target_type,
            )
            installation.target_id = target_id
            installation.target_type = target_type
            installation.save()
        if created and sync_repositories_on_create:
            installation.service.sync_repositories()
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
