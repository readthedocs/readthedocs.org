# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import mock
import six
from cryptography.hazmat.backends import openssl
from cryptography.hazmat.primitives import serialization
from django.test import TestCase
import django_dynamic_fixture as fixture

from readthedocs.projects.mixins import SSHKeyGenMixin
from readthedocs.projects.models import SSHKey
from readthedocs.projects.ssh import generate_ssh_pair_keys


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
