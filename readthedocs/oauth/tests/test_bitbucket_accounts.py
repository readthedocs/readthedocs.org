from unittest import mock

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.bitbucket_oauth2.provider import BitbucketOAuth2Provider
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.contrib.auth.models import User
from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.notifications.constants import CANCELLED
from readthedocs.notifications.constants import UNREAD
from readthedocs.notifications.models import Notification
from readthedocs.oauth.notifications import MESSAGE_OAUTH_BITBUCKET_RECONNECT
from readthedocs.oauth.signals import remove_bitbucket_accounts_without_account_id
from readthedocs.oauth.utils import get_bitbucket_accounts_without_account_id


class BitbucketAccountsWithoutAccountIdTest(TestCase):
    def setUp(self):
        self.user = get(User)

    def _account(self, uid, extra_data, provider=BitbucketOAuth2Provider.id, user=None):
        return get(
            SocialAccount,
            provider=provider,
            uid=uid,
            extra_data=extra_data,
            user=user or self.user,
        )

    def test_get_accounts_without_account_id(self):
        missing = self._account("missing", {"username": "missing"})
        null = self._account("null", {"account_id": None})
        self._account("557058:abc", {"account_id": "557058:abc"})
        self._account("1234", {}, provider=GitHubProvider.id)

        assert set(get_bitbucket_accounts_without_account_id()) == {missing, null}

    def test_remove_accounts_on_connect(self):
        missing = self._account("missing", {"username": "missing"})
        null = self._account("null", {"account_id": None})
        other = self._account("557058:other", {"account_id": "557058:other"})
        other_user = self._account("someone", {}, user=get(User))
        new = self._account("557058:abc", {"account_id": "557058:abc"})
        Notification.objects.add(
            message_id=MESSAGE_OAUTH_BITBUCKET_RECONNECT,
            attached_to=self.user,
            dismissable=True,
        )

        remove_bitbucket_accounts_without_account_id(
            sender=SocialLogin,
            request=mock.MagicMock(),
            sociallogin=SocialLogin(user=self.user, account=new),
        )

        remaining = set(SocialAccount.objects.all())
        assert missing not in remaining
        assert null not in remaining
        assert {other, other_user, new} <= remaining
        notification = Notification.objects.get(message_id=MESSAGE_OAUTH_BITBUCKET_RECONNECT)
        assert notification.state == CANCELLED

    def test_dont_remove_accounts_on_other_providers_connect(self):
        missing = self._account("missing", {"username": "missing"})
        github = self._account("1234", {}, provider=GitHubProvider.id)
        Notification.objects.add(
            message_id=MESSAGE_OAUTH_BITBUCKET_RECONNECT,
            attached_to=self.user,
            dismissable=True,
        )

        remove_bitbucket_accounts_without_account_id(
            sender=SocialLogin,
            request=mock.MagicMock(),
            sociallogin=SocialLogin(user=self.user, account=github),
        )

        assert SocialAccount.objects.filter(pk=missing.pk).exists()
        notification = Notification.objects.get(message_id=MESSAGE_OAUTH_BITBUCKET_RECONNECT)
        assert notification.state == UNREAD
