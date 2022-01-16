"""Community site-wide form overrides."""

import structlog

import requests

from allauth.account.forms import SignupForm
from django.conf import settings
from django import forms

log = structlog.get_logger(__name__)  # noqa


class SignupFormWithNewsletter(SignupForm):

    """Custom signup form that includes a checkbox to subscribe to a newsletter."""

    receive_newsletter = forms.BooleanField(
        required=False,
        label=(
            "Subscribe to our newsletter to get product updates."
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
            log.bind(
                user_email=self.cleaned_data["email"],
                user_username=user.username,
            )
            log.info('Subscribing user to newsletter.')

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
                log.warning('Timeout subscribing user to newsletter.')
            except Exception:  # noqa
                log.exception('Unknown error subscribing user to newsletter.')

        return user
