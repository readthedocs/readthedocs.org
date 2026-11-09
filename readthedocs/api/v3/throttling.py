from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.throttling import UserRateThrottle

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


class PollingUserRateThrottle(UserRateThrottle):
    """
    Looser throttle for endpoints the dashboard polls while a build runs.

    The build detail page requests the build and its notifications every
    few seconds, which sits at the default authenticated rate.
    """

    scope = "polling_user"


class PollingAnonRateThrottle(AnonRateThrottle):
    """
    Looser throttle for endpoints the dashboard polls while a build runs.

    Anonymous viewers poll less often than logged in users,
    but still more than the default anonymous rate allows.
    """

    scope = "polling_anon"
