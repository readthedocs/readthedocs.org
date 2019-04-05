# -*- coding: utf-8 -*-

import os
import mock

from mock import call
import django_dynamic_fixture as fixture
from django.test import TestCase
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django import urls

from readthedocs.builds.models import Version
from readthedocs.core.models import UserProfile
from readthedocs.projects.models import Project
from readthedocs.projects.tasks import remove_dirs


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

    @mock.patch('readthedocs.core.utils.general.broadcast')
    def test_wipe_selected_version(self, mock_broadcast):
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
        ]

        mock_broadcast.assert_has_calls(
            [
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[0],)]),
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[1],)]),
                call(type='build', task=remove_dirs, args=[(expected_del_dirs[2],)]),
            ],
            any_order=False
        )
