from django.contrib.auth import BACKEND_SESSION_KEY

from readthedocs.acl.constants import BACKEND_REQUEST_KEY


def get_auth_backend(request):
    """
    Get the current auth_backend used on this request.

    By default the full qualified name of the backend class
    is stored on the request session, but our internal
    backends set this as an attribute on the request object.
    """
    backend_auth = request.session.get(BACKEND_SESSION_KEY)
    backend_perm = getattr(request, BACKEND_REQUEST_KEY, None)
    return backend_auth or backend_perm
