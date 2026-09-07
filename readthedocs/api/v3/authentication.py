"""Authentication and throttling helpers for API V3."""

from rest_framework.authentication import TokenAuthentication
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle

from readthedocs.api.v2.permissions import TokenKeyParser


def has_project_api_key_header(request):
    """
    Whether the request carries something shaped like a project API key.

    User tokens and project API keys share the ``Token`` keyword, but user
    tokens are 40 hexadecimal characters, while project API keys are
    ``<prefix>.<secret>``. Used to avoid hitting the database for user tokens,
    and to tell apart "no key given" from "wrong key given".
    """
    key = TokenKeyParser().get(request)
    return bool(key) and "." in key


def get_project_api_key(request):
    """
    Return the project API key used to authenticate this request, if any.

    The key is injected by the ``HasProjectAPIKey`` permission class, so it's
    only present on views using it.
    """
    return getattr(request, "project_api_key", None)


class UserTokenAuthentication(TokenAuthentication):
    """
    Ignore project API keys so ``HasProjectAPIKey`` can handle them.

    Authentication runs before permissions, and the parent class raises
    ``AuthenticationFailed`` for anything that isn't a user token. Returning
    ``None`` lets the request continue as anonymous instead.
    """

    def authenticate(self, request):
        if has_project_api_key_header(request):
            return None
        return super().authenticate(request)


class ProjectAPIKeyUserRateThrottle(UserRateThrottle):
    """Throttle API key requests per key, instead of falling back to the client IP."""

    def get_cache_key(self, request, view):
        api_key = get_project_api_key(request)
        if api_key:
            return self.cache_format % {
                "scope": self.scope,
                "ident": f"apikey-{api_key.prefix}",
            }
        return super().get_cache_key(request, view)


class ProjectAPIKeyAnonRateThrottle(AnonRateThrottle):
    """Don't apply the anonymous rate to API key requests."""

    def get_cache_key(self, request, view):
        if get_project_api_key(request):
            return None
        return super().get_cache_key(request, view)
