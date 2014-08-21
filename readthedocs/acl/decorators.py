from functools import wraps
import logging

from django.contrib.auth import authenticate, login

from acl.models import ProjectAccessToken

log = logging.getLogger(__name__)


def token_access(fn):
    '''Check for a token and validate, applying the token to the request

    Using the token id found in the request session, validate a token object and
    apply it to the request, allowing views to use the validated token.
    '''

    @wraps(fn)
    def _wrapped(request, *args, **kwargs):
        token_id = request.session.get('access_token')
        token = ProjectAccessToken.get_validated_token(token_id)
        if token is not None:
            request.token = token
            user = authenticate(token_id=token_id)
            if user:
                login(request, user)

        return fn(request, *args, **kwargs)

    return _wrapped
