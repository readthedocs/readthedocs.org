# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

from django.contrib.auth.models import User
import mock
import six
from cryptography.hazmat.backends import openssl
from cryptography.hazmat.primitives import serialization
from django.test import TestCase
import django_dynamic_fixture as fixture


from readthedocs.projects.models import Project
from readthedocs.rtd_tests.base import MockBuildTestCase, RequestFactoryTestMixin

from .keys import generate_ssh_pair_keys
from .mixins import SSHKeyGenMixin
from .models import SSHKey
from .views import DetailKeysView, ListKeysView


class TestProjectKeyView(RequestFactoryTestMixin, MockBuildTestCase):

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


class SSHKeyModelTests(TestCase):

    def test_fingerprint(self):
        public_key = (
            'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDBFPEZe1XSoPsV9LOqzoPRe4pAWL'
            'W6+sPO3EWv+NFGSFEZh7BYA9T8B05boRkLhFqkmMMcDM1GOTqZ5cEB1rmJHWc7yYlZ'
            'MQbd4CwNSxD14HRoL5QSmM07QpwjhzpSHlKsb2HZCxpbmuXOcft940PrVZVP7rc+MI'
            'i6uBEF5HwalxazujW4eBHU8HRgACemjhaYScOeYJDfkjES4FyhW+En4w6ApO4RbRbP'
            'vnsoVDpf8I1oHHKx2INnixi4HsmGC4iTvemA4lZhthqHkbVAURx9qXnAqlfFSz2OHH'
            'GM/mxUeoUSEtUgq2B/2DXriFnwj/463gELCToPObNV0zi+ZozP '
            'support@readthedocs.org'
        )
        profile = fixture.get(SSHKey, public_key=public_key)
        self.assertEqual(
            profile.fingerprint,
            'e6:98:8f:4a:8e:a1:df:0f:f9:bb:c4:53:93:b5:78:34',
        )


class SSHKeyGenerationTests(TestCase):

    def test_valid_generate_pair_keys(self):
        """Check that the keys generated are valid."""
        private_str, public_str = generate_ssh_pair_keys()

        # Check strings are returned
        self.assertTrue(isinstance(public_str, six.text_type))
        self.assertTrue(isinstance(private_str, six.text_type))

        # Check loading those strings as private and public keys
        private_key = serialization.load_pem_private_key(
            private_str.encode('utf8'),
            password=None,
            backend=openssl.backend,
        )
        self.assertTrue(
            isinstance(private_key, openssl.rsa.RSAPrivateKeyWithSerialization),
        )

        public_key = serialization.load_ssh_public_key(
            public_str.encode('utf8'),
            openssl.backend,
        )
        self.assertTrue(
            isinstance(public_key, openssl.rsa.RSAPublicKeyWithSerialization),
        )

        # Generate public key from loaded private key and check it's
        # the same than the one returned by our own method
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
        public_string = '{key} {comment}'.format(
            key=public_bytes.decode('utf8'),
            comment='support@readthedocs.org',
        )
        self.assertEqual(public_string, public_str)

    def test_mixin_for_keys_generation(self):
        """Make sure the mixin calls the proper method."""
        mixin = SSHKeyGenMixin()
        mixin.save = mock.MagicMock()
        mixin.generate_keys(commit=False)
        mixin.save.assert_not_called()
        self.assertTrue(isinstance(mixin.public_key, six.text_type))
        self.assertTrue(isinstance(mixin.private_key, six.text_type))

        mixin.generate_keys(commit=True)
        mixin.save.assert_called_once()
