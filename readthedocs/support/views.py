"""Support views."""

import base64
import hashlib
import hmac
import logging

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.views import APIView

from readthedocs.core.utils.extend import SettingsOverrideObject

log = logging.getLogger(__name__)


class FrontAppClient:

    """Wrapper around Front's API."""

    BASE_URL = 'https://api2.frontapp.com'

    def __init__(self, token):
        self.token = token

    @property
    def _headers(self):
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        return headers

    def _get_url(self, path):
        return f'{self.BASE_URL}{path}'

    def get(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return requests.get(self._get_url(path), **kwargs)

    def patch(self, path, **kwargs):
        kwargs.setdefault('headers', {}).update(self._headers)
        return requests.patch(self._get_url(path), **kwargs)

class FrontAppWebhookBase(APIView):

    """
    Front's webhook handler.

    Currently we only listen to inbound messages events.
    Contact information is updated when a new message is received.

    See https://dev.frontapp.com/docs/webhooks-1.
    """

    http_method_names = ['post']

    def post(self, request):
        if not self._is_payload_valid():
            return Response(
                {'detail': 'Invalid payload'},
                status=HTTP_400_BAD_REQUEST,
            )

        event = request.data.get('type')
        if event == 'inbound':
            return self._update_contact_information(request.data)
        return Response({'detail': f'Skipping {event} event'})

    def _update_contact_information(self, data):
        """
        Update contact information using Front's API.

        The webhook event give us the conversation_id,
        we use that to retrieve the email from the user that originated
        the conversation, and finally we use the email to update
        the contact information (three API requests!).
        """
        client = FrontAppClient(token=settings.FRONTAPP_TOKEN)

        # Retrieve the user from the email from the conversation.
        conversation_id = data.get('conversation', {}).get('id')
        try:
            resp = client.get(f'/conversations/{conversation_id}').json()
            email = resp.get('recipient', {}).get('handle')
        except Exception:  # noqa
            msg = f'Error while getting conversation {conversation_id}'
            log.exception(msg)
            return Response({'detail': msg}, status=HTTP_500_INTERNAL_SERVER_ERROR)

        user = (
            User.objects
            .filter(Q(email=email) | Q(emailaddress__email=email))
            .first()
        )
        if not user:
            msg = f'User with email {email} not found in our database'
            log.info(msg)
            return Response({'detail': msg})

        # Get current custom fields, and update them.
        try:
            resp = client.get(f'/contacts/alt:email:{email}').json()
        except Exception:  # noqa
            msg = f'Error while getting contact {email}'
            log.exception(msg)
            return Response({'detail': msg}, HTTP_500_INTERNAL_SERVER_ERROR)

        new_custom_fields = self._get_custom_fields(user)
        custom_fields = resp.get('custom_fields', {})
        custom_fields.update(new_custom_fields)

        try:
            client.patch(
                f'/contacts/alt:email:{email}',
                json={'custom_fields': custom_fields}
            )
        except Exception:  # noqa
            msg = f'Error while updating contact information for {email}'
            log.exception(msg)
            return Response(
                {
                    'detail': msg,
                    'custom_fields': new_custom_fields,
                },
                status=HTTP_500_INTERNAL_SERVER_ERROR,
            )
        else:
            return Response({
                'detail': f'User updated {email}',
                'custom_fields': new_custom_fields,
            })

    # pylint: disable=no-self-use
    def _get_custom_fields(self, user):
        """
        Attach custom fields for this user.

        These fields need to be created on Front (settings -> Contacts -> Custom Fields).
        """
        custom_fields = {}
        custom_fields['org:username'] = user.username
        custom_fields['org:admin'] = f'{settings.ADMIN_URL}/auth/user/{user.pk}/change'
        return custom_fields

    def _is_payload_valid(self):
        """
        Check if the signature and the payload from the webhook matches.

        https://dev.frontapp.com/docs/webhooks-1#validating-data-integrity
        """
        digest = self._get_digest()
        signature = self.request.headers.get('X-Front-Signature', '')
        result = hmac.compare_digest(digest, signature.encode())
        return result

    def _get_digest(self):
        """Get a HMAC digest of the request using Front's API secret."""
        secret = settings.FRONTAPP_API_SECRET
        digest = hmac.new(
            secret.encode(),
            msg=self.request.body,
            digestmod=hashlib.sha1,
        )
        return base64.b64encode(digest.digest())


class FrontAppWebhook(SettingsOverrideObject):
    _default_class = FrontAppWebhookBase
