"""Allauth overrides."""

import json

import structlog
from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string
from django.utils.encoding import force_str

from readthedocs.core.utils import send_email
from readthedocs.invitations.models import Invitation

log = structlog.get_logger(__name__)


class AccountAdapter(DefaultAccountAdapter):

    """Customize Allauth emails to match our current patterns."""

    def format_email_subject(self, subject):
        return force_str(subject)

    def send_mail(self, template_prefix, email, context):
        subject = render_to_string(
            "{}_subject.txt".format(template_prefix),
            context,
        )
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)

        # Allauth sends some additional data in the context, remove it if the
        # pieces can't be json encoded
        removed_keys = []
        for key in list(context.keys()):
            try:
                _ = json.dumps(context[key])  # noqa for F841
            except (ValueError, TypeError):
                removed_keys.append(key)
                del context[key]
        if removed_keys:
            log.debug(
                "Removed context we were unable to serialize.",
                removed_keys=removed_keys,
            )

        send_email(
            recipient=email,
            subject=subject,
            template="{}_message.txt".format(template_prefix),
            template_html="{}_message.html".format(template_prefix),
            context=context,
        )

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
