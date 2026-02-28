from datetime import datetime, timedelta

from django.test import TestCase
from django_dynamic_fixture import get

from readthedocs.builds.constants import BRANCH, EXTERNAL, TAG
from readthedocs.builds.models import Version
from readthedocs.builds.tasks import delete_inactive_external_versions
from readthedocs.projects.models import Project


class TestTasks(TestCase):

    def test_delete_inactive_external_versions(self):
        project = get(Project)
        project.versions.all().delete()
        get(
            Version,
            project=project,
            slug='branch',
            type=BRANCH,
            active=False,
            modified=datetime.now() - timedelta(days=7),
        )
        get(
            Version,
            project=project,
            slug='tag',
            type=TAG,
            active=True,
            modified=datetime.now() - timedelta(days=7),
        )
        get(
            Version,
            project=project,
            slug='external-active',
            type=EXTERNAL,
            active=True,
            modified=datetime.now() - timedelta(days=7),
        )
        get(
            Version,
            project=project,
            slug='external-inactive',
            type=EXTERNAL,
            active=False,
            modified=datetime.now() - timedelta(days=3),
        )
        get(
            Version,
            project=project,
            slug='external-inactive-old',
            type=EXTERNAL,
            active=False,
            modified=datetime.now() - timedelta(days=7),
        )

        self.assertEqual(Version.objects.all().count(), 5)
        self.assertEqual(Version.external.all().count(), 3)

        # We don't have inactive external versions from 9 days ago.
        delete_inactive_external_versions(days=9)
        self.assertEqual(Version.objects.all().count(), 5)
        self.assertEqual(Version.external.all().count(), 3)

        # We have one inactive external versions from 6 days ago.
        delete_inactive_external_versions(days=6)
        self.assertEqual(Version.objects.all().count(), 4)
        self.assertEqual(Version.external.all().count(), 2)
        self.assertFalse(Version.objects.filter(slug='external-inactive-old').exists())
