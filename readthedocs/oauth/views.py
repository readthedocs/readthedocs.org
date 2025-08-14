import hmac

import structlog
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from readthedocs.api.v2.views.integrations import GITHUB_EVENT_HEADER
from readthedocs.api.v2.views.integrations import GITHUB_SIGNATURE_HEADER
from readthedocs.api.v2.views.integrations import WebhookMixin
from readthedocs.oauth.tasks import GitHubAppWebhookHandler
from readthedocs.oauth.tasks import handle_github_app_webhook


log = structlog.get_logger(__name__)


class GitHubAppWebhookView(APIView):
    """
    Handle GitHub App webhooks.

    This view is basically a wrapper around the `handle_github_app_webhook` task.
    This is done since several events may trigger a full sync of the installation's projects,
    and we want to avoid blocking the request or getting a timeout.
    """

    authentication_classes = []

    def post(self, request):
        if not self._is_payload_signature_valid():
            log.debug("Invalid webhook signature")
            raise ValidationError("Invalid webhook signature")

        # Most of the events have an installation object and action.
        installation_id = request.data.get("installation", {}).get("id", "unknown")
        action = request.data.get("action", "unknown")
        event = self.request.headers.get(GITHUB_EVENT_HEADER)
        # Unique identifiers for the event, useful to keep track of the event for debugging.
        # https://docs.github.com/en/webhooks/webhook-events-and-payloads#delivery-headers.
        event_id = self.request.headers.get("X-GitHub-Delivery", "unknown")
        structlog.contextvars.bind_contextvars(
            installation_id=installation_id,
            action=action,
            event=event,
            event_id=event_id,
        )
        if event not in GitHubAppWebhookHandler(request.data, event).event_handlers:
            log.info("Unsupported event")
            raise ValidationError(f"Unsupported event: {event}")

        log.info("Handling event")
        handle_github_app_webhook.delay(
            data=request.data,
            event=event,
            event_id=event_id,
        )
        return Response(status=200)

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
