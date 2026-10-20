from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from readthedocs.api.v3.models import RTDAPIKey


class RTDAPIKeyAuthentication(BaseAuthentication):
    """
    Authenticate requests using an API key (``RTDAPIKey``).

    Keys are passed using the same format as user tokens (``Authorization: Token <key>``),
    and are identified by their prefix (e.g. ``rtdorg_proj_``).
    Requests with a key without our prefix are left to other authentication classes.

    The request isn't attached to a user, ``request.user`` is an anonymous user
    and ``request.auth`` is the API key, views should check the key's permissions.
    """

    keyword = "Token"

    def authenticate(self, request):
        auth = get_authorization_header(request).decode(errors="replace").split()
        if len(auth) != 2 or auth[0].lower() != self.keyword.lower():
            return None

        key = auth[1]
        if not RTDAPIKey.objects.get_scope_from_key(key):
            return None

        try:
            api_key = RTDAPIKey.objects.get_from_key(key)
        except RTDAPIKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")

        if api_key.has_expired:
            raise AuthenticationFailed("API key has expired.")

        return AnonymousUser(), api_key

    def authenticate_header(self, request):
        return self.keyword
