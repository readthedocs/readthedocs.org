# -*- coding: utf-8 -*-
import django_dynamic_fixture as fixture
import mock
from django import urls
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.test import TestCase

from readthedocs.core.models import UserProfile
from readthedocs.projects.models import Project


class ProjectAdminActionsTest(TestCase):

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

    def setUp(self):
        self.client.force_login(self.admin)

    def test_project_ban_owner(self):
        self.assertFalse(self.owner.profile.banned)
        action_data = {
            ACTION_CHECKBOX_NAME: [self.project.pk],
            'action': 'ban_owner',
            'index': 0,
        }
        resp = self.client.post(
            urls.reverse('admin:projects_project_changelist'),
            action_data,
        )
        self.assertTrue(self.project.users.filter(profile__banned=True).exists())
        self.assertFalse(self.project.users.filter(profile__banned=False).exists())

    def test_project_ban_multiple_owners(self):
        owner_b = fixture.get(User)
        profile_b = fixture.get(UserProfile, user=owner_b, banned=False)
        self.project.users.add(owner_b)
        self.assertFalse(self.owner.profile.banned)
        self.assertFalse(owner_b.profile.banned)
        action_data = {
            ACTION_CHECKBOX_NAME: [self.project.pk],
            'action': 'ban_owner',
            'index': 0,
        }
        resp = self.client.post(
            urls.reverse('admin:projects_project_changelist'),
            action_data,
        )
        self.assertFalse(self.project.users.filter(profile__banned=True).exists())
        self.assertEqual(self.project.users.filter(profile__banned=False).count(), 2)

    @mock.patch('readthedocs.projects.admin.clean_project_resources')
    def test_project_delete(self, clean_project_resources):
        """Test project and artifacts are removed."""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.project.pk],
            'action': 'delete_selected',
            'index': 0,
            'post': 'yes',
        }
        resp = self.client.post(
            urls.reverse('admin:projects_project_changelist'),
            action_data,
        )
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())
        clean_project_resources.assert_has_calls([
            mock.call(
                self.project,
            ),
        ])
