from unittest import mock

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import get_adapter as get_social_account_adapter
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, override_settings
from django_dynamic_fixture import get

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider


class SocialAdapterTest(TestCase):
    def setUp(self):
        self.user = get(User, username="test")
        self.adapter = get_social_account_adapter()

    @override_settings(RTD_ALLOW_GITHUB_APP=False)
    def test_dont_allow_using_githubapp_for_non_staff_users(self):
        assert not SocialAccount.objects.filter(provider=GitHubAppProvider.id).exists()

        # Anonymous user
        request = mock.MagicMock(user=AnonymousUser())
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(provider=GitHubAppProvider.id),
        )
        with self.assertRaises(ImmediateHttpResponse) as exc:
            self.adapter.pre_social_login(request, sociallogin)
        self.assertEqual(exc.exception.response.status_code, 302)

        assert not SocialAccount.objects.filter(provider=GitHubAppProvider.id).exists()

        # Existing non-staff user
        assert not self.user.is_staff
        request = mock.MagicMock(user=self.user)
        sociallogin = SocialLogin(
            user=User(email="me@example.com"),
            account=SocialAccount(provider=GitHubAppProvider.id),
        )
        with self.assertRaises(ImmediateHttpResponse) as exc:
            self.adapter.pre_social_login(request, sociallogin)
        self.assertEqual(exc.exception.response.status_code, 302)
        assert not self.user.socialaccount_set.filter(
            provider=GitHubAppProvider.id
        ).exists()

    @override_settings(RTD_ALLOW_GITHUB_APP=True)
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
