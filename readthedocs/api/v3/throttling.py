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


class PollingRateThrottle(SimpleRateThrottle):
    """
    Looser throttle for endpoints the dashboard polls while a build runs.

    The build detail page requests the build and its notifications every
    few seconds, which exceeds the default anonymous rate.
    Limits are per user, or per IP for anonymous requests.
    """

    scope = "polling"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {"scope": self.scope, "ident": ident}
