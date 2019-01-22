# -*- coding: utf-8 -*-

import mock

from django import urls
import django_dynamic_fixture as fixture
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.test import TestCase
from django.conf import settings
from messages_extends.models import Message as PersistentMessage

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

    @mock.patch('readthedocs.projects.admin.broadcast')
    def test_project_delete(self, broadcast):
        """Test project and artifacts are removed."""
        from readthedocs.projects.tasks import remove_dirs
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
        broadcast.assert_has_calls([
            mock.call(
                type='app', task=remove_dirs, args=[(self.project.doc_path,)],
            ),
        ])

    @mock.patch('readthedocs.projects.admin.send_email')
    def test_request_namespace(self, mock_send_email):
        """Test the requesting of project's namespace"""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.project.pk],
            'action': 'request_namespace',
        }
        resp = self.client.post(
            urls.reverse('admin:projects_project_changelist'),
            action_data
        )

        proj = self.project
        self.assertEqual(proj.users.get_queryset().count(), 1)
        user = proj.users.get_queryset().first()

        mock_send_email.assert_called_once_with(
            recipient=user.email,
            subject='Rename request for abandoned project', 
            template='projects/email/abandon_project.txt', 
            template_html='projects/email/abandon_project.html',
            context={'proj_name': proj.name} 
        )

    @mock.patch('readthedocs.projects.admin.broadcast')
    @mock.patch('readthedocs.notifications.backends.send_email')
    def test_mark_as_abandoned(self, mock_send_email, mock_broadcast):
        """Test the marking of project as abandoned."""
        from readthedocs.projects.tasks import rename_project_dir

        project = fixture.get(Project, users=[self.admin])
        action_data = {
            ACTION_CHECKBOX_NAME: [project.pk],
            'action': 'mark_as_abandoned',
        }

        # before marking project as abandoned.
        current_slug = project.slug
        current_doc_path = project.doc_path
        self.assertEqual(project.users.get_queryset().count(), 1)
        user = project.users.get_queryset().first()

        self.assertEqual(PersistentMessage.objects.count(), 0)
     
        resp = self.client.post(
            urls.reverse('admin:projects_project_changelist'),
            action_data,
        )

        project.refresh_from_db()

        # after marking the project as abandoned.
        new_doc_path = project.doc_path
        new_slug = '{}-abandoned'.format(current_slug)

        self.assertEqual(
            project.get_absolute_url(),
            '/projects/{}/'.format(new_slug)
        )
        new_url = '{base}{url}'.format(
            base=settings.PRODUCTION_DOMAIN,
            url=project.get_absolute_url()
        )

        self.assertTrue(project.is_abandoned, True)
        self.assertEqual(project.slug, new_slug)
        mock_broadcast.assert_called_once_with(
            type='web',
            task=rename_project_dir,
            args=[current_doc_path, new_doc_path]
        )
        failure_message = _(
            'Your project {name} is marked as abandoned. Update link '
            'for the project docs is <a href="{url}">{url}</a>.'
        )
        # user must have to notified via email.
        mock_send_email.assert_has_calls([
            mock.call(
                template='core/email/common.txt',
                context={'content': failure_message.format(name=project.name, url=new_url)},
                subject=u'Abandoned project {}'.format(project.name),
                template_html='core/email/common.html',
                recipient=user.email,
                request=None
            )
        ])
        # Persistent error msg is added to notify user.
        self.assertEqual(PersistentMessage.objects.filter(read=False).count(), 1)
