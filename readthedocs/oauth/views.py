import hmac

import structlog
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.views.integrations import (
    GITHUB_EVENT_HEADER,
    GITHUB_SIGNATURE_HEADER,
    WebhookMixin,
)
from readthedocs.oauth.models import GitHubAppInstallation
from readthedocs.oauth.services.githubapp import GitHubAppService

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
        action = data.get("action")
        installation = data.get("installation", {})

        if action == "created":
            gha_installation, _ = self._get_or_create_installation(installation, data)
            # We do a full sync, since it's a new installation.
            GitHubAppService(gha_installation).sync_repositories()
        elif action == "deleted":
            gha_installation = GitHubAppInstallation.objects.filter(
                installation_id=installation["id"]
            ).first()
            if not gha_installation:
                # If we never created the installation, we can ignore the event.
                # Maybe don't raise an error?
                raise ValidationError(f"Installation {installation['id']} not found")
            gha_installation.delete()

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
        action = data.get("action")
        installation = data.get("installation", {})
        gha_installation, created = self._get_or_create_installation(installation, data)
        service = GitHubAppService(gha_installation)

        if created:
            # If we didn't have the installation, we do a full sync.
            service.sync_repositories()
            return

        if action == "added":
            if data["repository_selection"] == "all":
                service.sync_repositories()
            else:
                service.add_repositories(
                    [repo["id"] for repo in data["repositories_added"]]
                )
        elif action == "removed":
            service.remove_repositories(
                [repo["id"] for repo in data["repositories_removed"]]
            )

        raise ValidationError(f"Unsupported action: {action}")

    def _handle_installation_target_event(self):
        """
        Handle the installation_target event.

        Triggered when the target of an installation changes,
        like when the user or organization changes its username/slug.
        """

    def _get_or_create_installation(self, installation: dict, extra_data: dict):
        target_id = installation["target_id"]
        target_type = installation["target_type"]
        installation, created = GitHubAppInstallation.objects.get_or_create(
            installation_id=installation["id"],
            defaults={
                "extra_data": extra_data,
                "target_id": target_id,
                "target_type": target_type,
            },
        )
        # NOTE: An installation can't change its target_id or target_type.
        # This should never happen, unless our assumptions are wrong.
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
