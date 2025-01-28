from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_dynamic_fixture import get

from readthedocs.api.v2.models import BuildAPIKey
from readthedocs.api.v2.tasks import delete_old_revoked_build_api_keys
from readthedocs.projects.models import Project


class TestTasks(TestCase):
    def test_delete_revoked_keys(self):
        project = get(Project)
        created_more_than_a_week_ago = timezone.now() - timedelta(days=8)

        revoked_key = get(
            BuildAPIKey, project=project, revoked=True, name="revoked key"
        )
        expired_key = get(
            BuildAPIKey,
            project=project,
            expiry_date=timezone.now() - timedelta(days=1),
            name="expired key",
        )
        valid_key = get(BuildAPIKey, project=project, name="valid key")

        revoked_old_key = get(
            BuildAPIKey,
            project=project,
            revoked=True,
            created=created_more_than_a_week_ago,
            name="revoked old key",
        )
        expired_old_key = get(
            BuildAPIKey,
            project=project,
            expiry_date=timezone.now() - timedelta(days=1),
            created=created_more_than_a_week_ago,
            name="expired old key",
        )
        valid_old_key = get(
            BuildAPIKey,
            project=project,
            created=created_more_than_a_week_ago,
            name="valid old key",
        )

        self.assertEqual(BuildAPIKey.objects.count(), 6)
        delete_old_revoked_build_api_keys(days=7)
        self.assertEqual(BuildAPIKey.objects.count(), 4)
        deleted_keys = [
            expired_old_key,
            revoked_old_key,
        ]
        self.assertFalse(
            BuildAPIKey.objects.filter(pk__in=[key.pk for key in deleted_keys]).exists()
        )
