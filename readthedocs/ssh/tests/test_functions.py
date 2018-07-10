# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals

import mock
import six
from cryptography.hazmat.backends import openssl
from cryptography.hazmat.primitives import serialization
from django.test import TestCase

from ..keys import generate_ssh_pair_keys
from ..mixins import SSHKeyGenMixin


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
