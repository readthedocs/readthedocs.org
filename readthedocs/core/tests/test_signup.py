from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from django.conf import settings
from django.test import TestCase


class TestNewsletterSignup(TestCase):
    def setUp(self):
        self.form_data = {
            "email": "test123@gmail.com",
            "username": "test123",
            "password1": "123456",
            "password2": "123456",
        }
        self.form_data_plus_checkbox = self.form_data.copy()
        self.form_data_plus_checkbox["receive_newsletter"] = True

    @patch("readthedocs.core.signals.requests.post")
    def test_signup_without_checkbox_does_not_subscribe(self, mock_requests_post):
        response = self.client.post("/accounts/signup/", data=self.form_data)
        email_confirmed.send(
            sender=None,
            request=None,
            email_address=EmailAddress.objects.get(email=self.form_data["email"]),
        )

        mock_requests_post.assert_not_called()

    @patch("readthedocs.core.signals.requests.post")
    def test_signup_calls_subscribe_api(self, mock_requests_post):
        response = self.client.post(
            "/accounts/signup/", data=self.form_data_plus_checkbox
        )
        email_confirmed.send(
            sender=None,
            request=None,
            email_address=EmailAddress.objects.get(email=self.form_data["email"]),
        )

        mock_requests_post.assert_called_with(
            settings.MAILERLITE_API_SUBSCRIBERS_URL,
            json={
                "email": self.form_data["email"],
                "resubscribe": True,
            },
            headers={"X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY},
            timeout=3,
        )
