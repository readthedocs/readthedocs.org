'''Custom backend to allow anonymous token access'''

import logging

from django.conf import settings

from core.models import AuthenticatedAnonymousUser
from projects.models import AccessToken
from projects.constants import ACCESS_READONLY

log = logging.getLogger(__name__)


class TokenAccessBackend(object):
    '''Authenticate an anonymous user against a token

    Using a token id, authenticate an anonymous user and apply permissions for
    viewing builds to the user.
    '''

    def authenticate(self, token_id):
        token = AccessToken.objects.get(token=token_id)
        if token and token.is_valid():
            user = AuthenticatedAnonymousUser()
            user.token = token
            return user
        return None

    def get_user(self, uid):
        return None

    def has_perm(self, user, perm, obj=None):
        if not hasattr(user, 'token'):
            return None
        if user.token is not None and user.token.is_valid():
            if user.token.project == obj:
                if (perm == 'builds.view_version' and
                        user.token.access_level == ACCESS_READONLY):
                    return True
            else:
                log.error('Unauthorized token access with token {0}'
                          .format(user.token))
                return False
        return None
