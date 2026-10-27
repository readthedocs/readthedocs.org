from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from readthedocs.api.v3.models import RTDToken


class RTDTokenAuthentication(TokenAuthentication):
    """
    Authenticate requests using an API token (``RTDToken``).

    Tokens are passed using the same format as user tokens (``Authorization: Token <token>``),
    and are identified by their prefix (e.g. ``rtdorg_project_``).
    Requests with a token without our prefix are left to other authentication classes.

    The request isn't attached to a user, ``request.user`` is an anonymous user
    and ``request.auth`` is the API token, views should check the token's permissions.
    """

    model = RTDToken

    def authenticate_credentials(self, key):
        if not self.model.objects.get_scope_from_key(key):
            # Not one of our tokens, let other authentication classes handle it.
            return None

        try:
            token = self.model.objects.get_from_key(key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid token."))

        if token.has_expired:
            raise exceptions.AuthenticationFailed(_("Token has expired."))

        self.update_last_used(token)
        return AnonymousUser(), token

    def update_last_used(self, token):
        # This is a write on every request, API tokens are only used by the upload API for now,
        # which doesn't get many requests. If this becomes a problem,
        # only update it if the last update was more than x minutes ago.
        now = timezone.now()
        token.last_used_at = now
        # Use update to not change the modified date of the token.
        self.model.objects.filter(pk=token.pk).update(last_used_at=now)
