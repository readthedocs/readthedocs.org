from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from readthedocs.notifications.models import Notification
from readthedocs.subscriptions.constants import TYPE_CONCURRENT_BUILDS
from readthedocs.subscriptions.products import RTDProductFeature

from .mixins import APIEndpointMixin


@override_settings(
    RTD_ALLOW_ORGANIZATIONS=False,
    ALLOW_PRIVATE_REPOS=False,
    RTD_DEFAULT_FEATURES=dict(
        [RTDProductFeature(TYPE_CONCURRENT_BUILDS, value=4).to_item()]
    ),
)
class UsersEndpointTests(APIEndpointMixin):
    def test_users_list(self):
        # We don't have this endpoint enabled on purpose
        with self.assertRaises(NoReverseMatch) as e:
            reverse("users-list")

    def test_users_detail(self):
        # We don't have this endpoint enabled on purpose
        with self.assertRaises(NoReverseMatch) as e:
            reverse(
                "users-detail",
                kwargs={
                    "user_username": self.me.username,
                },
            )

    def test_users_notifications_list(self):
        url = reverse(
            "users-notifications-list",
            kwargs={
                "parent_lookup_user__username": self.me.username,
            },
        )

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("users-notifications-list"),
        )

    def test_users_notifications_list_with_email_like_username(self):
        """Test for #11260."""
        self.me.username = "test@example.com"
        self.me.save()
        url = reverse(
            "users-notifications-list",
            kwargs={
                "parent_lookup_user__username": self.me.username,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_users_notifications_list_other_user(self):
        url = reverse(
            "users-notifications-list",
            kwargs={
                "parent_lookup_user__username": self.me.username,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_users_notifications_list_post(self):
        url = reverse(
            "users-notifications-list",
            kwargs={
                "parent_lookup_user__username": self.me.username,
            },
        )

        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(url)

        # We don't allow POST on this endpoint
        self.assertEqual(response.status_code, 405)

    def test_users_notifications_detail(self):
        url = reverse(
            "users-notifications-detail",
            kwargs={
                "parent_lookup_user__username": self.me.username,
                "notification_pk": self.notification_user.pk,
            },
        )

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertDictEqual(
            response.json(),
            self._get_response_dict("users-notifications-detail"),
        )

    def test_users_notifications_detail_other(self):
        url = reverse(
            "users-notifications-detail",
            kwargs={
                "parent_lookup_user__username": self.me.username,
                "notification_pk": self.notification_user.pk,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_users_notifications_detail_patch(self):
        url = reverse(
            "users-notifications-detail",
            kwargs={
                "parent_lookup_user__username": self.me.username,
                "notification_pk": self.notification_user.pk,
            },
        )
        data = {
            "state": "read",
        }

        self.client.logout()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)

        notification = Notification.objects.get(
            attached_to_content_type=ContentType.objects.get_for_model(self.me),
            attached_to_id=self.me.pk,
        )

        self.assertEqual(notification.state, "unread")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 204)

        notification.refresh_from_db()
        self.assertEqual(notification.state, "read")
