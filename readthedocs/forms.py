"""Community site-wide form overrides."""

import json
import logging

import requests

from allauth.account.forms import SignupForm
from django.conf import settings
from django.forms.fields import BooleanField

log = logging.getLogger(__name__)  # noqa


class SignupFormWithNewsletter(SignupForm):

    """Custom signup form that includes a checkbox to subscribe to a newsletter."""

    receive_newsletter = BooleanField(
        required=False,
        label=(
            "I also wish to subscribe to the Read the Docs newsletter "
            "to receive news and updates regularly. "
            "I know I can unsubscribe at any time."
        ),
    )

    field_order = [
        'email',
        'username',
        'password1',
        'password2',
        'receive_newsletter',
    ]

    def save(self, request):
        user = super().save(request)

        if self.cleaned_data.get("receive_newsletter"):
            log.info('Subscribing user to newsletter. email=%s', self.cleaned_data["email"])

            url = settings.MAILERLITE_API_SUBSCRIBERS_URL
            payload = json.dumps({
                'email': self.cleaned_data["email"],
            })
            headers = {
                'Content-Type': "application/json",
                'X-MailerLite-ApiKey': settings.MAILERLITE_API_KEY,
            }
            try:
                resp = requests.post(
                    url,
                    data=payload,
                    headers=headers,
                    timeout=3,  # seconds
                )
            except requests.Timeout:
                log.warning('Timeout subscribing user to newsletter')

            if resp and not resp.ok:
                log.exception('Unknown error subscribing user to newsletter')

        return user
