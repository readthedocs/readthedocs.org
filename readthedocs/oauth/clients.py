from datetime import datetime
from datetime import timedelta

import structlog
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from github import Auth
from github import GithubIntegration
from github import GithubRetry
from requests_oauthlib import OAuth2Session


log = structlog.get_logger(__name__)


def _get_token_updater(token):
    """
    Update token given data from OAuth response.

    Expect the following response into the closure::

        {
            u'token_type': u'bearer',
            u'scopes': u'webhook repository team account',
            u'refresh_token': u'...',
            u'access_token': u'...',
            u'expires_in': 3600,
            u'expires_at': 1449218652.558185
        }
    """

    def _updater(data):
        token.token = data["access_token"]
        token.token_secret = data.get("refresh_token", "")
        token.expires_at = timezone.make_aware(
            datetime.fromtimestamp(data["expires_at"]),
        )
        token.save()
        log.info("Updated token.", token_id=token.pk)

    return _updater


def get_oauth2_client(account):
    """Get an OAuth2 client for the given social account."""
    token = account.socialtoken_set.first()
    if token is None:
        return None

    token_config = {
        "access_token": token.token,
        "token_type": "bearer",
    }
    if token.expires_at is not None:
        token_expires = (token.expires_at - timezone.now()).total_seconds()
        token_config.update(
            {
                "refresh_token": token.token_secret,
                "expires_in": token_expires,
            }
        )

    provider = account.get_provider()
    social_app = provider.app
    oauth2_adapter = provider.get_oauth2_adapter(request=provider.request)

    session = OAuth2Session(
        client_id=social_app.client_id,
        token=token_config,
        auto_refresh_kwargs={
            "client_id": social_app.client_id,
            "client_secret": social_app.secret,
        },
        auto_refresh_url=oauth2_adapter.access_token_url,
        token_updater=_get_token_updater(token),
    )
    return session


def get_gh_app_client() -> GithubIntegration:
    """Return a client authenticated as the GitHub App to interact with the API."""
    app_auth = Auth.AppAuth(
        app_id=settings.GITHUB_APP_CLIENT_ID,
        private_key=settings.GITHUB_APP_PRIVATE_KEY,
        # 10 minutes is the maximum allowed by GitHub.
        # PyGithub will handle the token expiration and renew it automatically.
        jwt_expiry=60 * 10,
    )
    return GithubIntegration(
        auth=app_auth,
        # Fetch the maximum number of items per page (default is 30),
        # so paginated requests consume less of the API rate limit.
        per_page=100,
        # Interacting with a nested resource doesn't make an extra
        # request to fetch the parent resource, which saves API calls.
        lazy=True,
        # PyGitHub's retry will respect the GitHub API rate limit headers and retry after the specified time.
        # We set a maximum wait time in case GitHub returns a very long wait time.
        retry=GithubRetry(
            # PyGithub arguments
            secondary_rate_wait=15,
            max_rate_limit_wait=15,
            # urllib3 Retry arguments.
            total=5,
        ),
    )


# Stop using a cached installation token this long before GitHub expires it,
# so a request never goes out with a token that is about to expire.
GH_APP_INSTALLATION_TOKEN_EXPIRY_MARGIN = timedelta(minutes=5)


def _get_gh_installation_token_cache_key(installation_id: int) -> str:
    return f"github-app-installation-token:{installation_id}"


def invalidate_gh_installation_token(installation_id: int):
    """Remove the cached access token of the given installation, so the next request mints a new one."""
    cache.delete(_get_gh_installation_token_cache_key(installation_id))


class CachedAppInstallationAuth(Auth.AppInstallationAuth):
    """
    Authenticate as a GitHub App installation, sharing the access token through Django's cache.

    PyGithub only keeps the token on the auth object, so every new client
    (one per task) used to request a new token from GitHub.
    Installation tokens are valid for one hour and can be used concurrently,
    so we share them between processes until shortly before they expire.

    See https://docs.github.com/en/rest/apps/apps#create-an-installation-access-token-for-an-app.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token = None
        self._token_expires_at = None

    @property
    def cache_key(self) -> str:
        return _get_gh_installation_token_cache_key(self.installation_id)

    @property
    def token(self) -> str:
        if self._token is None or self._token_expires_at <= timezone.now():
            self._token, self._token_expires_at = self._get_token()
        return self._token

    def _get_token(self) -> tuple[str, datetime]:
        cached = cache.get(self.cache_key)
        if cached:
            return cached["token"], cached["expires_at"]

        authorization = self._get_installation_authorization()
        expires_at = authorization.expires_at - GH_APP_INSTALLATION_TOKEN_EXPIRY_MARGIN
        timeout = (expires_at - timezone.now()).total_seconds()
        if timeout > 0:
            cache.set(
                self.cache_key,
                {"token": authorization.token, "expires_at": expires_at},
                timeout=int(timeout),
            )
        return authorization.token, expires_at

    def invalidate(self):
        """Discard the token, so the next request mints a new one."""
        invalidate_gh_installation_token(self.installation_id)
        self._token = None
        self._token_expires_at = None
