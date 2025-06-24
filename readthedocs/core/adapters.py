"""Allauth overrides."""

import structlog
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_str

from readthedocs.allauth.providers.githubapp.provider import GitHubAppProvider
from readthedocs.core.utils import send_email_from_object
from readthedocs.invitations.models import Invitation


log = structlog.get_logger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    """Customize Allauth emails to match our current patterns."""

    def format_email_subject(self, subject):
        return force_str(subject)

    def render_mail(self, template_prefix, email, context, headers=None):
        """
        Wrapper around render_mail to send emails using a task.

        ``send_email`` makes use of the email object returned by this method,
        and calls ``send`` on it. We override this method to return a dummy
        object that has a ``send`` method, which in turn calls our task to send
        the email.
        """
        email = super().render_mail(template_prefix, email, context, headers=headers)

        class DummyEmail:
            def __init__(self, email):
                self.email = email

            def send(self):
                send_email_from_object(self.email)

        return DummyEmail(email)

    def save_user(self, request, user, form, commit=True):
        """Override default account signup to redeem invitations at sign-up."""
        user = super().save_user(request, user, form)

        invitation_pk = request.session.get("invitation:pk")
        if invitation_pk:
            invitation = Invitation.objects.pending().filter(pk=invitation_pk).first()
            if invitation:
                log.info("Redeeming invitation at sign-up", invitation_pk=invitation_pk)
                invitation.redeem(user, request=request)
                invitation.delete()
            else:
                log.info("Invitation not found", invitation_pk=invitation_pk)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        self._filter_email_addresses(sociallogin)
        self._block_use_of_old_github_oauth_app(request, sociallogin)
        self._connect_github_app_to_existing_github_account(request, sociallogin)

    def _filter_email_addresses(self, sociallogin):
        """
        Remove all email addresses except the primary one.

        We don't want to populate all email addresses from the social account,
        it also makes it easy to mark only the primary email address as verified
        for providers that don't return information about email verification
        even if the email is verified (like GitLab).
        """
        sociallogin.email_addresses = [
            email for email in sociallogin.email_addresses if email.primary
        ]

    def _connect_github_app_to_existing_github_account(self, request, sociallogin):
        """
        Connect a GitHub App (new integration) account to an existing GitHub account (old integration).

        When a user signs up with the GitHub App we check if there is an existing GitHub account,
        and if it belongs to the same user, we connect the accounts instead of creating a new one.
        """
        provider = sociallogin.account.get_provider()

        # If the provider is not GitHub App, nothing to do.
        if provider.id != GitHubAppProvider.id:
            return

        # If the user already signed up with the GitHub App, nothing to do.
        if sociallogin.is_existing:
            return

        social_account = SocialAccount.objects.filter(
            provider=GitHubProvider.id,
            uid=sociallogin.account.uid,
        ).first()

        # If there is an existing GH account, we check if that user can use the GH App,
        # otherwise we check for the current user.
        user_to_check = social_account.user if social_account else request.user
        if not self._can_use_github_app(user_to_check):
            raise ImmediateHttpResponse(HttpResponseRedirect(reverse("account_login")))

        # If there isn't an existing GH account, nothing to do,
        # just let allauth create the new account.
        if not social_account:
            return

        # If the user is logged in, and the GH OAuth account belongs to
        # a different user, we should not connect the accounts,
        # this is the same as trying to connect an existing GH account to another user.
        if request.user.is_authenticated and request.user != social_account.user:
            message_template = "socialaccount/messages/account_connected_other.txt"
            get_account_adapter(request).add_message(
                request=request,
                level=messages.ERROR,
                message_template=message_template,
            )
            url = reverse("socialaccount_connections")
            raise ImmediateHttpResponse(HttpResponseRedirect(url))

        sociallogin.connect(request, social_account.user)

    def _can_use_github_app(self, user):
        """
        Check if the user can use the GitHub App.

        Only staff users can use the GitHub App for now.
        """
        return settings.RTD_ALLOW_GITHUB_APP or user.is_staff

    def _block_use_of_old_github_oauth_app(self, request, sociallogin):
        """
        Block the use of the old GitHub OAuth app if the user is already using the new GitHub App.

        This is a temporary measure to block the use of the old GitHub OAuth app
        until we switch our login to always use the new GitHub App.

        If the user has its account still connected to the old GitHub OAuth app,
        we allow them to use it, since there is no difference between using the two apps
        for logging in.
        """
        provider = sociallogin.account.get_provider()

        # If the provider is not GitHub, nothing to do.
        if provider.id != GitHubProvider.id:
            return

        # If the user is still using the old GitHub OAuth app, nothing to do.
        if sociallogin.is_existing:
            return

        has_gh_app_social_account = SocialAccount.objects.filter(
            provider=GitHubAppProvider.id,
            uid=sociallogin.account.uid,
        ).exists()

        # If there is no existing GitHub App account, nothing to do.
        if not has_gh_app_social_account:
            return

        # Show a warning to the user and redirect them to the GitHub App login page.
        messages.warning(
            request,
            "You already migrated from our old GitHub OAuth app. "
            "Click below to sign in with the new GitHub App.",
        )
        url = reverse("githubapp_login")
        raise ImmediateHttpResponse(HttpResponseRedirect(url))
