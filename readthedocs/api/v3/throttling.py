from rest_framework import throttling

from readthedocs.api.v3.models import RTDAPIKey


class UserRateThrottle(throttling.UserRateThrottle):
    """Throttle requests authenticated with an API key using the user rate, by key."""

    def get_cache_key(self, request, view):
        if isinstance(request.auth, RTDAPIKey):
            return self.cache_format % {
                "scope": self.scope,
                "ident": f"api-key-{request.auth.prefix}",
            }
        return super().get_cache_key(request, view)


class AnonRateThrottle(throttling.AnonRateThrottle):
    """Don't throttle requests authenticated with an API key as anonymous requests."""

    def get_cache_key(self, request, view):
        if isinstance(request.auth, RTDAPIKey):
            return None
        return super().get_cache_key(request, view)
