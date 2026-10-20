from django.contrib.auth.models import AnonymousUser
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from readthedocs.api.v3.models import RTDAPIKey


class RTDAPIKeyAuthentication(TokenAuthentication):
    """
    Authenticate requests using an API key (``RTDAPIKey``).

    Keys are passed using the same format as user tokens (``Authorization: Token <key>``),
    and are identified by their prefix (e.g. ``rtdorg_project_``).
    Requests with a key without our prefix are left to other authentication classes.

    The request isn't attached to a user, ``request.user`` is an anonymous user
    and ``request.auth`` is the API key, views should check the key's permissions.
    """

    model = RTDAPIKey

    def authenticate_credentials(self, key):
        if not self.model.objects.get_scope_from_key(key):
            # Not one of our keys, let other authentication classes handle it.
            return None

        try:
            api_key = self.model.objects.get_from_key(key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        if api_key.has_expired:
            raise exceptions.AuthenticationFailed(_("Token has expired."))

        return AnonymousUser(), api_key
