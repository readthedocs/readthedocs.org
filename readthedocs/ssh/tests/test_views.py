# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import User
import mock
import django_dynamic_fixture as fixture
from io import StringIO

from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import RequestFactoryTestMixin

from .utils import PRIVATE_KEY_STRING

from ..models import SSHKey
from ..views import DetailKeysView, ListKeysView, GenerateKeysView, UploadKeysView, DeleteKeysView


# ``ssh`` is installed but URLs are not defined
@override_settings(ROOT_URLCONF='readthedocs.ssh.tests.urls')
class SSHKeyProjectAdminViewTests(RequestFactoryTestMixin, TestCase):

    def setUp(self):
        self.user = fixture.get(User)
        self.project = fixture.get(
            Project,
            slug='foobar',
            users=[self.user],
        )
        self.key = fixture.get(
            SSHKey,
            project=self.project,
        )

    def test_list_view(self):
        req = self.request(
            '/dashboard/foobar/keys/',
            user=self.user,
        )
        resp = ListKeysView.as_view()(req, project_slug=self.project.slug)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context_data['project'], self.project)
        self.assertEqual(
            list(self.project.sshkeys.values_list('pk', flat=True)),
            [s.pk for s in resp.context_data['sshkey_list']],
        )
        self.assertEqual(len(resp.context_data['sshkey_list']), 1)

    def test_detail_view(self):
        key_pk = self.project.sshkeys.first().pk
        req = self.request(
            '/dashboard/foobar/keys/{0}'.format(key_pk),
            user=self.user,
        )
        resp = DetailKeysView.as_view()(req,
                                        key_pk=key_pk,
                                        project_slug=self.project.slug)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context_data['project'], self.project)
        self.assertEqual(resp.context_data['sshkey'],
                         self.project.sshkeys.get(pk=key_pk))

    def test_generate_view(self):
        self.assertEqual(self.project.sshkeys.count(), 1)
        req = self.request(
            '/dashboard/foobar/keys/generate',
            method='post',
            user=self.user,
        )
        resp = GenerateKeysView.as_view()(
            req,
            project_slug=self.project.slug,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/dashboard/foobar/keys/')
        self.assertEqual(self.project.sshkeys.count(), 2)
        key = self.project.sshkeys.last()
        self.assertIsNotNone(key.private_key)
        self.assertIsNotNone(key.public_key)

    def test_upload_view(self):
        self.assertEqual(self.project.sshkeys.count(), 1)
        private_key_file = StringIO(PRIVATE_KEY_STRING)
        req = self.request(
            '/dashboard/foobar/keys/upload',
            method='post',
            user=self.user,
            data={'private_key': private_key_file},
        )
        resp = UploadKeysView.as_view()(
            req,
            project_slug=self.project.slug,
        )


        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/dashboard/foobar/keys/')
        self.assertEqual(self.project.sshkeys.count(), 2)
        key = self.project.sshkeys.last()
        self.assertEqual(key.private_key, PRIVATE_KEY_STRING)
        self.assertIsNotNone(key.public_key)

        req = self.request(
            '/dashboard/foobar/keys/upload',
            method='post',
            user=self.user,
            data={'private_key': 'invalid private key'},
        )
        resp = UploadKeysView.as_view()(
            req,
            project_slug=self.project.slug,
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.project.sshkeys.count(), 2)

    @mock.patch('readthedocs.ssh.views.SSHKey.service_id', new_callable=mock.PropertyMock)
    def test_delete_view(self, service_id):
        service_id.return_value = None

        key_pk = self.project.sshkeys.first().pk
        self.assertEqual(self.project.sshkeys.count(), 1)
        req = self.request(
            '/dashboard/foobar/keys/{0}/delete'.format(key_pk),
            method='post',
            user=self.user,
        )
        resp = DeleteKeysView.as_view()(
            req,
            key_pk=key_pk,
            project_slug=self.project.slug,
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, '/dashboard/foobar/keys/')
        self.assertEqual(self.project.sshkeys.count(), 0)
