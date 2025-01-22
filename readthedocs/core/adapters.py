"""Allauth overrides."""

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider

import structlog
from allauth.account.adapter import DefaultAccountAdapter
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
        provider = sociallogin.account.get_provider()
        if provider.id == GitHubAppProvider.id and not sociallogin.is_existing:
            social_ccount = SocialAccount.objects.filter(
                provider=GitHubProvider.id,
                uid=sociallogin.account.uid,
            ).first()
            if social_ccount:
                sociallogin.connect(request, social_ccount.user)
