import django_dynamic_fixture as fixture
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse

from readthedocs.notifications.constants import CANCELLED, DISMISSED
from readthedocs.notifications.models import Notification
from readthedocs.projects.notifications import MESSAGE_PROJECT_SKIP_BUILDS
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
class NotificationsEndpointTests(APIEndpointMixin):
    def test_notifications_list(self):
        url = reverse("notifications-list")

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("notifications-list"),
        )

        # Adding a CANCELLED/DISMISSED notification won't be returned on this endpoint
        fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(self.project),
            attached_to_id=self.project.id,
            message_id=MESSAGE_PROJECT_SKIP_BUILDS,
            state=CANCELLED,
        )

        fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(self.project),
            attached_to_id=self.project.id,
            message_id=MESSAGE_PROJECT_SKIP_BUILDS,
            state=DISMISSED,
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("notifications-list"),
        )

    def test_notifications_list_post(self):
        url = reverse("notifications-list")

        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(url)

        # We don't allow POST on this endpoint
        self.assertEqual(response.status_code, 405)
