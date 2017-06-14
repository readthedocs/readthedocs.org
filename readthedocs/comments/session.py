"""Authentication backends for DRF."""

from __future__ import absolute_import
from rest_framework.authentication import SessionAuthentication


class UnsafeSessionAuthentication(SessionAuthentication):

    def authenticate(self, request):
        http_request = request._request  # pylint: disable=protected-access
        user = getattr(http_request, 'user', None)

        if not user or not user.is_active:
            return None

        return (user, None)
