"""Community site-wide form overrides."""

import logging

import requests

from allauth.account.forms import SignupForm
from django.conf import settings
from django import forms

log = logging.getLogger(__name__)  # noqa


class SignupFormWithNewsletter(SignupForm):

    """Custom signup form that includes a checkbox to subscribe to a newsletter."""

    receive_newsletter = forms.BooleanField(
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
            log.info(
                'Subscribing user to newsletter. email=%s, user=%s',
                self.cleaned_data["email"],
                user.username,
            )

            url = settings.MAILERLITE_API_SUBSCRIBERS_URL
            payload = {
                'email': self.cleaned_data["email"],
                'resubscribe': True,
            }
            headers = {
                'X-MailerLite-ApiKey': settings.MAILERLITE_API_KEY,
            }
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=3,  # seconds
                )
                resp.raise_for_status()
            except requests.Timeout:
                log.warning(
                    'Timeout subscribing user to newsletter. email=%s, user=%s',
                    self.cleaned_data["email"],
                    user.username,
                )
            except Exception:  # noqa
                log.exception(
                    'Unknown error subscribing user to newsletter. email=%s, user=%s',
                    self.cleaned_data["email"],
                    user.username,
                )

        return user
