import os
from unittest import mock

import django_dynamic_fixture as fixture
from django import urls
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.builds.models import Version
from readthedocs.core.models import UserProfile
from readthedocs.projects.models import Project


class VersionAdminActionsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.owner = fixture.get(User)
        cls.profile = fixture.get(UserProfile, user=cls.owner, banned=False)
        cls.admin = fixture.get(User, is_staff=True, is_superuser=True)
        cls.project = fixture.get(
            Project,
            main_language_project=None,
            users=[cls.owner],
        )
        cls.version = fixture.get(Version, project=cls.project)

    def setUp(self):
        self.client.force_login(self.admin)

    @mock.patch('readthedocs.core.utils.general.remove_dirs')
    def test_wipe_selected_version(self, remove_dirs):
        action_data = {
            ACTION_CHECKBOX_NAME: [self.version.pk],
            'action': 'wipe_selected_versions',
            'post': 'yes',
        }
        resp = self.client.post(
            urls.reverse('admin:builds_version_changelist'),
            action_data
        )
        expected_del_dirs = [
            os.path.join(self.version.project.doc_path, 'checkouts', self.version.slug),
            os.path.join(self.version.project.doc_path, 'envs', self.version.slug),
            os.path.join(self.version.project.doc_path, 'conda', self.version.slug),
            os.path.join(self.version.project.doc_path, '.cache'),
        ]

        remove_dirs.assert_called_with(expected_del_dirs)
