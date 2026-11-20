from datetime import timedelta
from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.builds.constants import BUILD_STATE_FINISHED
from readthedocs.builds.models import Build
from readthedocs.core.tasks import subscribe_active_users_to_newsletter
from readthedocs.projects.models import Project


@override_settings(
    MAILERLITE_API_ONBOARDING_GROUP_URL="https://mailerlite.example/group",
    MAILERLITE_API_KEY="mlkey",
)
class TestOnboardingSignup(TestCase):
    def setUp(self):
        self.form_data = {
            "email": "test123@gmail.com",
            "username": "test123",
            "password1": "123456",
            "password2": "123456",
        }
        self.form_data_plus_checkbox = self.form_data.copy()
        self.form_data_plus_checkbox["receive_newsletter"] = True

    def confirm_email(self):
        email_confirmed.send(
            sender=None,
            request=None,
            email_address=EmailAddress.objects.get(email=self.form_data["email"]),
        )

    @patch("readthedocs.core.signals.requests.post")
    def test_signup_without_checkbox_does_not_subscribe(self, mock_requests_post):
        self.client.post("/accounts/signup/", data=self.form_data)
        self.confirm_email()

        mock_requests_post.assert_not_called()

    @patch("readthedocs.core.signals.requests.post")
    def test_signup_adds_to_onboarding_group(self, mock_requests_post):
        self.client.post("/accounts/signup/", data=self.form_data_plus_checkbox)
        self.confirm_email()

        mock_requests_post.assert_called_once_with(
            "https://mailerlite.example/group",
            json={
                "email": self.form_data["email"],
                "resubscribe": True,
                "type": "active",
            },
            headers={"X-MailerLite-ApiKey": "mlkey"},
            timeout=3,
        )


@override_settings(BUTTONDOWN_API_KEY="key")
@patch("readthedocs.core.tasks.requests.post")
class TestSubscribeActiveUsersToNewsletter(TestCase):
    def setUp(self):
        self.user = get(User, email="user@example.com")
        self.user.profile.mailing_list = True
        self.user.profile.save()
        get(EmailAddress, user=self.user, email=self.user.email, verified=True)
        self.project = get(Project, users=[self.user], skip=False)

    def add_build(self, days_ago=0, success=True):
        build = get(
            Build,
            project=self.project,
            version=self.project.versions.first(),
            state=BUILD_STATE_FINISHED,
            success=success,
        )
        # `date` is auto_now_add, so update it after creation.
        Build.objects.filter(pk=build.pk).update(date=timezone.now() - timedelta(days=days_ago))

    def test_subscribes_user_after_first_successful_build(self, mock_requests_post):
        self.add_build()
        subscribe_active_users_to_newsletter()

        mock_requests_post.assert_called_once_with(
            settings.BUTTONDOWN_API_SUBSCRIBERS_URL,
            json={"email_address": "user@example.com", "type": "regular"},
            headers={"Authorization": "Token key"},
            timeout=5,
        )

    def test_skips_user_without_successful_build(self, mock_requests_post):
        self.add_build(success=False)
        subscribe_active_users_to_newsletter()

        mock_requests_post.assert_not_called()

    def test_skips_user_with_earlier_successful_build(self, mock_requests_post):
        self.add_build(days_ago=5)
        self.add_build()
        subscribe_active_users_to_newsletter()

        mock_requests_post.assert_not_called()

    def test_skips_user_not_opted_in(self, mock_requests_post):
        self.user.profile.mailing_list = False
        self.user.profile.save()
        self.add_build()
        subscribe_active_users_to_newsletter()

        mock_requests_post.assert_not_called()

    def test_skips_banned_user(self, mock_requests_post):
        self.user.profile.banned = True
        self.user.profile.save()
        self.add_build()
        subscribe_active_users_to_newsletter()

        mock_requests_post.assert_not_called()

    def test_skips_unverified_email(self, mock_requests_post):
        EmailAddress.objects.filter(user=self.user).update(verified=False)
        self.add_build()
        subscribe_active_users_to_newsletter()

        mock_requests_post.assert_not_called()

    def test_skips_inactive_project(self, mock_requests_post):
        self.project.skip = True
        self.project.save()
        self.add_build()
        subscribe_active_users_to_newsletter()

        mock_requests_post.assert_not_called()
