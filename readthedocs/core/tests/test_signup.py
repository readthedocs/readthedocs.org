from http import HTTPStatus
from unittest.mock import patch

import requests
import requests_mock

from django.test import TestCase
from django.conf import settings

from readthedocs.forms import SignupFormWithNewsletter


class TestNewsletterSignup(TestCase):
    form_data = {
        "email": "test123@gmail.com",
        "username": "test123",
        "password1": "123456",
        "password2": "123456",
    }
    form_data_plus_checkbox = form_data.copy()
    form_data_plus_checkbox["receive_newsletter"] = True

    @patch("readthedocs.forms.requests.post")
    def test_signup_without_checkbox_does_not_subscribe(self, mock_requests_post):
        response = self.client.post("/accounts/signup/", data=self.form_data)

        assert response.status_code == HTTPStatus.FOUND

        mock_requests_post.assert_not_called()


    @patch("readthedocs.forms.requests.post")
    def test_signup_with_checkbox_calls_subscribe_api(self, mock_requests_post):
        response = self.client.post("/accounts/signup/", data=self.form_data_plus_checkbox)

        assert response.status_code == HTTPStatus.FOUND, response

        mock_requests_post.assert_called_with(
            settings.MAILERLITE_API_SUBSCRIBERS_URL,
            json={
                "email": self.form_data_plus_checkbox["email"],
                "resubscribe": True,
            },
            headers={"X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY},
            timeout=3,
        )

    @requests_mock.Mocker(kw='mock_request')
    def test_signup_with_checkbox_succeeds_if_timeout(self, mock_request):
        mock_request.post(settings.MAILERLITE_API_SUBSCRIBERS_URL, exc=requests.Timeout)

        response = self.client.post("/accounts/signup/", data=self.form_data_plus_checkbox)

        assert response.status_code == HTTPStatus.FOUND, response

    @requests_mock.Mocker(kw='mock_request')
    def test_signup_with_checkbox_succeeds_if_bad_response(self, mock_request):
        mock_request.post(settings.MAILERLITE_API_SUBSCRIBERS_URL, status_code=400)

        response = self.client.post("/accounts/signup/", data=self.form_data_plus_checkbox)

        assert response.status_code == HTTPStatus.FOUND, response
