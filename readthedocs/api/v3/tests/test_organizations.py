import django_dynamic_fixture as fixture
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from readthedocs.notifications.models import Notification
from readthedocs.organizations.models import Organization
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
class OrganizationsEndpointTests(APIEndpointMixin):
    def test_organizations_list(self):
        # We don't have this endpoint enabled on purpose
        with self.assertRaises(NoReverseMatch) as e:
            reverse("organizations-list")

    def test_organizations_detail(self):
        # We don't have this endpoint enabled on purpose
        with self.assertRaises(NoReverseMatch) as e:
            reverse(
                "organizations-detail",
                kwargs={
                    "organization_slug": self.organization.slug,
                },
            )

    def test_organizations_notifications_list(self):
        url = reverse(
            "organizations-notifications-list",
            kwargs={
                "parent_lookup_organization__slug": self.organization.slug,
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
            self._get_response_dict("organizations-notifications-list"),
        )

    def test_organizations_notifications_list_only_given_organization(self):
        url = reverse(
            "organizations-notifications-list",
            kwargs={
                "parent_lookup_organization__slug": self.organization.slug,
            },
        )
        other_organization = fixture.get(
            Organization,
            pub_date=self.created,
            modified_date=self.modified,
            name="other_organization",
            slug="other_organization",
            owners=[self.me],
        )

        fixture.get(
            Notification,
            attached_to_content_type=ContentType.objects.get_for_model(
                other_organization
            ),
            attached_to_id=other_organization.pk,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            self._get_response_dict("organizations-notifications-list"),
        )

    def test_organizations_notifications_list_other_user(self):
        url = reverse(
            "organizations-notifications-list",
            kwargs={
                "parent_lookup_organization__slug": self.organization.slug,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_organizations_notifications_list_post(self):
        url = reverse(
            "organizations-notifications-list",
            kwargs={
                "parent_lookup_organization__slug": self.organization.slug,
            },
        )

        self.client.logout()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.post(url)

        # We don't allow POST on this endpoint
        self.assertEqual(response.status_code, 405)

    def test_organizations_notifications_detail(self):
        url = reverse(
            "organizations-notifications-detail",
            kwargs={
                "parent_lookup_organization__slug": self.organization.slug,
                "notification_pk": self.notification_organization.pk,
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
            self._get_response_dict("organizations-notifications-detail"),
        )

    def test_organizations_notifications_detail_other_organization(self):
        other_organization = fixture.get(
            Organization,
            pub_date=self.created,
            modified_date=self.modified,
            name="new_org",
            slug="new_org",
            owners=[self.me],
        )

        url = reverse(
            "organizations-notifications-detail",
            kwargs={
                "parent_lookup_organization__slug": other_organization.slug,
                "notification_pk": self.notification_organization.pk,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_organizations_notifications_detail_other(self):
        url = reverse(
            "organizations-notifications-detail",
            kwargs={
                "parent_lookup_organization__slug": self.organization.slug,
                "notification_pk": self.notification_organization.pk,
            },
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.others_token.key}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_organizations_notifications_detail_patch(self):
        url = reverse(
            "organizations-notifications-detail",
            kwargs={
                "parent_lookup_organization__slug": self.organization.slug,
                "notification_pk": self.notification_organization.pk,
            },
        )
        data = {
            "state": "read",
        }

        self.client.logout()
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 401)

        self.assertEqual(self.organization.notifications.first().state, "unread")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.organization.notifications.first().state, "read")
