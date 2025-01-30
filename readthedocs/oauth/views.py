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

log = structlog.get_logger(__name__)


class GitHubAppWebhookView(APIView):
    authentication_classes = []

    def post(self, request):
        if not self._is_payload_signature_valid():
            raise ValidationError("Invalid webhook signature")

        event = self.request.headers.get(GITHUB_EVENT_HEADER)

        event_handlers = {
            "installation": self._handle_installation_event,
        }
        if event in event_handlers:
            event_handlers[event]()
            return Response(status=200)
        raise ValidationError(f"Unsupported event: {event}")

    def _handle_installation_event(self):
        """

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
            gha__installation, created = GitHubAppInstallation.objects.get_or_create(
                installation_id=installation["id"],
                target_id=installation["target_id"],
                target_type=installation["target_type"],
                extra_data=data,
            )
            # Sync repositories with the installation
            # Do we do an incremental sync or a full sync?
        elif action == "deleted":
            gha_installation = GitHubAppInstallation.objects.filter(
                installation_id=installation["id"]
            ).first()
            if not gha_installation:
                raise ValidationError(f"Installation {installation['id']} not found")

        raise ValidationError(f"Unsupported action: {action}")

    def _sync_installation_repositories(self, installation):
        pass

    def _add_installation_repositories(
        self, installation: GitHubAppInstallation, repositories: list[dict]
    ):
        pass

    def _remove_installation_repositories(self, installation, repositories):
        pass

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
