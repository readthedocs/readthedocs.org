from rest_framework.throttling import SimpleRateThrottle

from readthedocs.api.v3.models import RTDToken


class RTDTokenRateThrottle(SimpleRateThrottle):
    """Throttle requests authenticated with an API token, per token."""

    scope = "rtd_token"

    def get_cache_key(self, request, view):
        if not isinstance(request.auth, RTDToken):
            return None

        return self.cache_format % {
            "scope": self.scope,
            "ident": request.auth.prefix,
        }
