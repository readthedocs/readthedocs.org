import mock
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import get

from readthedocs.builds.forms import VersionForm
from readthedocs.builds.models import Version
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.models import Project


class TestVersionForm(TestCase):

    def setUp(self):
        self.user = get(User)
        self.project = get(Project, users=(self.user,))

    def test_default_version_is_active(self):
        version = get(
            Version,
            project=self.project,
            active=False,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                'active': True,
                'privacy_level': PRIVATE,
            },
            instance=version,
        )
        self.assertTrue(form.is_valid())

    def test_default_version_is_inactive(self):
        version = get(
            Version,
            project=self.project,
            active=True,
        )
        self.project.default_version = version.slug
        self.project.save()

        form = VersionForm(
            {
                'active': False,
                'privacy_level': PRIVATE,
            },
            instance=version,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('active', form.errors)

    @mock.patch('readthedocs.projects.tasks.clean_project_resources')
    def test_resources_are_deleted_when_version_is_inactive(self, clean_project_resources):
        version = get(
            Version,
            project=self.project,
            active=True,
        )

        url = reverse('project_version_detail', args=(version.project.slug, version.slug))

        self.client.force_login(self.user)

        r = self.client.post(
            url,
            data={
                'active': True,
                'privacy_level': PRIVATE,
            },
        )
        self.assertTrue(r.status_code, 200)
        clean_project_resources.assert_not_called()

        r = self.client.post(
            url,
            data={
                'active': False,
                'privacy_level': PRIVATE,
            },
        )
        self.assertTrue(r.status_code, 200)
        clean_project_resources.assert_called_once()
