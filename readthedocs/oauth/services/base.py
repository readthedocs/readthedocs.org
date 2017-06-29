"""OAuth utility functions"""

from __future__ import absolute_import
from builtins import str
from builtins import object
import logging
from datetime import datetime

from django.conf import settings
from requests_oauthlib import OAuth2Session
from allauth.socialaccount.models import SocialAccount


DEFAULT_PRIVACY_LEVEL = getattr(settings, 'DEFAULT_PRIVACY_LEVEL', 'public')

log = logging.getLogger(__name__)


class Service(object):

    """Service mapping for local accounts

    :param user: User to use in token lookup and session creation
    :param account: :py:class:`SocialAccount` instance for user
    """

    adapter = None
    url_pattern = None

    def __init__(self, user, account):
        self.session = None
        self.user = user
        self.account = account

    @classmethod
    def for_user(cls, user):
        """Return a list of instances if user has an account for the provider"""
        try:
            accounts = SocialAccount.objects.filter(
                user=user,
                provider=cls.adapter.provider_id
            )
            return [cls(user=user, account=account) for account in accounts]
        except SocialAccount.DoesNotExist:
            return []

    def get_adapter(self):
        return self.adapter

    @property
    def provider_id(self):
        return self.get_adapter().provider_id

    def get_session(self):
        if self.session is None:
            self.create_session()
        return self.session

    def create_session(self):
        """Create OAuth session for user

        This configures the OAuth session based on the :py:class:`SocialToken`
        attributes. If there is an ``expires_at``, treat the session as an auto
        renewing token. Some providers expire tokens after as little as 2
        hours.
        """
        token = self.account.socialtoken_set.first()
        if token is None:
            return None

        token_config = {
            'access_token': str(token.token),
            'token_type': 'bearer',
        }
        if token.expires_at is not None:
            token_expires = (token.expires_at - datetime.now()).total_seconds()
            token_config.update({
                'refresh_token': str(token.token_secret),
                'expires_in': token_expires,
            })

        self.session = OAuth2Session(
            client_id=token.app.client_id,
            token=token_config,
            auto_refresh_kwargs={
                'client_id': token.app.client_id,
                'client_secret': token.app.secret,
            },
            auto_refresh_url=self.get_adapter().access_token_url,
            token_updater=self.token_updater(token)
        )

        return self.session or None

    def token_updater(self, token):
        """Update token given data from OAuth response

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
            token.token = data['access_token']
            token.expires_at = datetime.fromtimestamp(data['expires_at'])
            token.save()
            log.info('Updated token %s:', token)

        return _updater

    def sync(self):
        raise NotImplementedError

    def create_repository(self, fields, privacy=DEFAULT_PRIVACY_LEVEL,
                          organization=None):
        raise NotImplementedError

    def create_organization(self, fields):
        raise NotImplementedError

    def setup_webhook(self, project):
        raise NotImplementedError

    def update_webhook(self, project, integration):
        raise NotImplementedError

    @classmethod
    def is_project_service(cls, project):
        """Determine if this is the service the project is using

        .. note::
            This should be deprecated in favor of attaching the
            :py:class:`RemoteRepository` to the project instance. This is a slight
            improvement on the legacy check for webhooks
        """
        # TODO Replace this check by keying project to remote repos
        return (
            cls.url_pattern is not None and
            cls.url_pattern.search(project.repo) is not None
        )
