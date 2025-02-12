"""Allauth overrides."""


import structlog
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
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
        """
        Additional logic to apply before social login.

        - Remove all email addresses except the primary one.

          We don't want to populate all email addresses from the social account,
          it also makes it easy to mark only the primary email address as verified
          for providers that don't return information about email verification
          even if the email is verified (like GitLab).

        - Connect a GitHub App (new integration) account to an existing GitHub account (old integration)
          if it belongs to the same user. This avoids creating a new account when the user
          signs up with the new integration.
        """
        sociallogin.email_addresses = [
            email for email in sociallogin.email_addresses if email.primary
        ]

        provider = sociallogin.account.get_provider()
        if provider.id == GitHubAppProvider.id and not sociallogin.is_existing:
            social_account = SocialAccount.objects.filter(
                provider=GitHubProvider.id,
                uid=sociallogin.account.uid,
            ).first()
            # No existing GitHub account found, nothing to do.
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
