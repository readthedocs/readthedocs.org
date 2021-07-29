from django.contrib.auth import BACKEND_SESSION_KEY

from readthedocs.acl.constants import BACKEND_REQUEST_KEY


def get_auth_backend(request):
    backend_auth = request.session.get(BACKEND_SESSION_KEY)
    backend_perm = getattr(request, BACKEND_REQUEST_KEY, None)
    return backend_auth or backend_perm
