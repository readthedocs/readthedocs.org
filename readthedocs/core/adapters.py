"""Allauth overrides"""

from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string

from readthedocs.core.utils import send_email

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class AccountAdapter(DefaultAccountAdapter):

    """Customize Allauth emails to match our current patterns"""

    def format_email_subject(self, subject):
        return force_text(subject)

    def send_mail(self, template_prefix, email, context):
        subject = render_to_string(
            '{0}_subject.txt'.format(template_prefix), context
        )
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)

        send_email(
            recipient=email,
            subject=subject,
            template='{0}_message.txt'.format(template_prefix),
            template_html='{0}_message.html'.format(template_prefix),
            context=context
        )
