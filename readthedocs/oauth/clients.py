from datetime import datetime

import structlog
from django.conf import settings
from django.utils import timezone
from github import Auth
from github import GithubIntegration
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
    return GithubIntegration(auth=app_auth)
