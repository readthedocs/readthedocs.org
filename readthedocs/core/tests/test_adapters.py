from unittest import mock

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import get_adapter as get_social_account_adapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.bitbucket_oauth2.provider import BitbucketOAuth2Provider
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider


class SocialAdapterTest(TestCase):
    def setUp(self):
        self.user = get(User, username="test")
        self.adapter = get_social_account_adapter()

    def test_allow_using_githubapp_for_all_users(self):
        assert not self.user.is_staff

        request = mock.MagicMock(user=self.user)
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(provider=GitHubAppProvider.id),
        )
        self.adapter.pre_social_login(request, sociallogin)
        # No exception raised, but the account is not created, as that is done in another step by allauth.
        assert not self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

    def test_allow_using_githubapp_for_staff_users(self):
        self.user.is_staff = True
        self.user.save()
        assert self.user.is_staff

        request = mock.MagicMock(user=self.user)
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(provider=GitHubAppProvider.id),
        )
        self.adapter.pre_social_login(request, sociallogin)
        # No exception raised, but the account is not created, as that is done in another step by allauth.
        assert not self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

    def test_connect_to_existing_github_account_from_staff_user(self):
        self.user.is_staff = True
        self.user.save()
        assert self.user.is_staff
        assert not self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

        github_account = get(
            SocialAccount,
            provider=GitHubProvider.id,
            uid="1234",
            user=self.user,
        )

        request = mock.MagicMock(user=AnonymousUser())
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(
                provider=GitHubAppProvider.id, uid=github_account.uid
            ),
        )
        self.adapter.pre_social_login(request, sociallogin)
        # A new user is not created, but the existing user is connected to the GitHub App.
        assert self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

    def test_connect_to_existing_github_account_from_staff_user_logged_in(self):
        self.user.is_staff = True
        self.user.save()
        assert self.user.is_staff
        assert not self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

        github_account = get(
            SocialAccount,
            provider=GitHubProvider.id,
            uid="1234",
            user=self.user,
        )

        request = mock.MagicMock(user=self.user)
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(
                provider=GitHubAppProvider.id, uid=github_account.uid
            ),
        )
        self.adapter.pre_social_login(request, sociallogin)
        # A new user is not created, but the existing user is connected to the GitHub App.
        assert self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

    def test_dont_connect_to_existing_github_account_if_user_is_logged_in_with_different_account(
        self,
    ):
        self.user.is_staff = True
        self.user.save()
        assert self.user.is_staff
        assert not self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

        github_account = get(
            SocialAccount,
            provider=GitHubProvider.id,
            uid="1234",
            user=self.user,
        )

        another_user = get(User, username="another")
        request = mock.MagicMock(user=another_user)
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(
                provider=GitHubAppProvider.id, uid=github_account.uid
            ),
        )
        with self.assertRaises(ImmediateHttpResponse) as exc:
            self.adapter.pre_social_login(request, sociallogin)
        self.assertEqual(exc.exception.response.status_code, 302)
        assert not self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()
        assert not another_user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

    def test_allow_existing_githubapp_accounts_to_login(self):
        assert not self.user.is_staff
        githubapp_account = get(
            SocialAccount,
            provider=GitHubAppProvider.id,
            uid="1234",
            user=self.user,
        )

        request = mock.MagicMock(user=AnonymousUser())
        sociallogin = SocialLogin(
            user=self.user,
            account=githubapp_account,
        )
        self.adapter.pre_social_login(request, sociallogin)

        self.user.is_staff = True
        self.user.save()
        assert self.user.is_staff
        self.adapter.pre_social_login(request, sociallogin)

    def test_dont_allow_using_old_github_app(self):
        github_app_account = get(
            SocialAccount,
            provider=GitHubAppProvider.id,
            uid="1234",
            user=self.user,
        )

        request = mock.MagicMock(user=AnonymousUser())
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(
                provider=GitHubProvider.id, uid=github_app_account.uid
            ),
        )
        with self.assertRaises(ImmediateHttpResponse) as exc:
            self.adapter.pre_social_login(request, sociallogin)

        assert self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()
        assert not self.user.socialaccount_set.filter(
            provider=GitHubProvider.id
        ).exists()

        response = exc.exception.response
        assert response.status_code == 302
        assert response.url == "/accounts/githubapp/login/"

    def test_allow_using_old_github_app(self):
        get(
            SocialAccount,
            provider=GitHubAppProvider.id,
            uid="1234",
            user=self.user,
        )
        github_account = get(
            SocialAccount,
            provider=GitHubProvider.id,
            uid="1234",
            user=self.user,
        )

        request = mock.MagicMock(user=AnonymousUser())
        sociallogin = SocialLogin(
            user=self.user,
            account=github_account,
        )
        self.adapter.pre_social_login(request, sociallogin)

        assert self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()
        assert self.user.socialaccount_set.filter(
            provider=GitHubProvider.id
        ).exists()


class BitbucketLegacyUidTest(TestCase):
    def setUp(self):
        self.user = get(User, username="test")
        self.adapter = get_social_account_adapter()
        self.request = mock.MagicMock(user=AnonymousUser())

    def _sociallogin(self, account_id, username):
        return SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(
                provider=BitbucketOAuth2Provider.id,
                uid=account_id,
                extra_data={"account_id": account_id, "username": username},
            ),
        )

    def test_migrate_legacy_uid_on_login(self):
        legacy = get(
            SocialAccount,
            provider=BitbucketOAuth2Provider.id,
            uid="old-username",
            extra_data={"account_id": "557058:abc", "username": "old-username"},
            user=self.user,
        )
        sociallogin = self._sociallogin("557058:abc", "new-username")
        self.adapter.pre_social_login(self.request, sociallogin)

        legacy.refresh_from_db()
        assert legacy.uid == "557058:abc"
        assert legacy.extra_data["username"] == "new-username"
        assert sociallogin.is_existing
        assert sociallogin.user == self.user
        assert sociallogin.account == legacy

    def test_dont_match_by_username(self):
        legacy = get(
            SocialAccount,
            provider=BitbucketOAuth2Provider.id,
            uid="claimed-username",
            extra_data={"account_id": "557058:victim", "username": "claimed-username"},
            user=self.user,
        )
        sociallogin = self._sociallogin("557058:attacker", "claimed-username")
        self.adapter.pre_social_login(self.request, sociallogin)

        legacy.refresh_from_db()
        assert legacy.uid == "claimed-username"
        assert not sociallogin.is_existing

    def test_skip_duplicated_account_ids(self):
        for username in ["first", "second"]:
            get(
                SocialAccount,
                provider=BitbucketOAuth2Provider.id,
                uid=username,
                extra_data={"account_id": "557058:abc", "username": username},
            )
        sociallogin = self._sociallogin("557058:abc", "third")
        self.adapter.pre_social_login(self.request, sociallogin)

        assert set(
            SocialAccount.objects.filter(provider=BitbucketOAuth2Provider.id).values_list(
                "uid", flat=True
            )
        ) == {"first", "second"}
        assert not sociallogin.is_existing

    def test_redirect_login_of_account_without_account_id(self):
        get(EmailAddress, user=self.user, email="me@example.com", verified=False)
        get(
            SocialAccount,
            provider=BitbucketOAuth2Provider.id,
            uid="old-username",
            extra_data={"username": "old-username"},
            user=self.user,
        )
        sociallogin = self._sociallogin("557058:abc", "new-username")
        sociallogin.email_addresses = [EmailAddress(email="Me@example.com", verified=False)]

        with self.assertRaises(ImmediateHttpResponse) as exc:
            self.adapter.pre_social_login(self.request, sociallogin)
        assert exc.exception.response.url == reverse("account_login")

    def test_redirect_login_of_account_with_null_account_id(self):
        self.user.email = "me@example.com"
        self.user.save()
        get(
            SocialAccount,
            provider=BitbucketOAuth2Provider.id,
            uid="old-username",
            extra_data={"account_id": None, "username": "old-username"},
            user=self.user,
        )
        sociallogin = self._sociallogin("557058:abc", "new-username")

        with self.assertRaises(ImmediateHttpResponse):
            self.adapter.pre_social_login(self.request, sociallogin)

    def test_dont_redirect_login_if_accounts_have_account_id(self):
        self.user.email = "me@example.com"
        self.user.save()
        get(
            SocialAccount,
            provider=BitbucketOAuth2Provider.id,
            uid="557058:other",
            extra_data={"account_id": "557058:other"},
            user=self.user,
        )
        sociallogin = self._sociallogin("557058:abc", "new-username")
        # No exception raised, allauth continues with the signup.
        self.adapter.pre_social_login(self.request, sociallogin)
        assert not sociallogin.is_existing

    def test_dont_redirect_when_connecting_account(self):
        self.user.email = "me@example.com"
        self.user.save()
        get(
            SocialAccount,
            provider=BitbucketOAuth2Provider.id,
            uid="old-username",
            extra_data={"username": "old-username"},
            user=self.user,
        )
        sociallogin = self._sociallogin("557058:abc", "new-username")
        request = mock.MagicMock(user=self.user)
        self.adapter.pre_social_login(request, sociallogin)
