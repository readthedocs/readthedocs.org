# -*- coding: utf-8 -*-
"""
Keys manipulation.

Utilities to create, generate and validate keys.
"""
from __future__ import division, print_function, unicode_literals

from cryptography.hazmat.backends import openssl
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from readthedocs.core.utils import get_support_email


def generate_ssh_pair_keys(key_size=2048, comment=None):
    """
    Generate SSH Public/Private key.

    :param key_size: size used to generated the key
    :param comment: optional comment to append to public key (by default the
        value returned by ``get_support_email`` is appended)

    :returns: tuple of private and public keys as strings

    :rtype: tuple(str, str)
    """
    # TODO: if the public key is generated from a private key, maybe we don't
    # want to add a default message
    comment = comment or get_support_email()

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=openssl.backend,
    )

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_string = private_bytes.decode('utf8')

    public_string = generate_public_from_private_key(
        private_key,
        text_format=False,
        comment=comment,
    )
    return private_string, public_string


def generate_public_from_private_key(
        private_key,
        text_format=False,
        comment=None,
):  # pylint: disable=invalid-name
    """
    Generate a public key given a private key.

    :param private_key: private key to generate public key from
    :type private_key: str or
        cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey

    :param text_format: whether or not the ``private_key`` param is in text
        format
    :type text_format: bool

    :param comment: optional comment to append to the public key (by default the
        value returned by ``get_support_email`` is appended)

    :returns: valid public key generated from the private key
    :rtype: str
    """
    if text_format:
        private_key = serialization.load_pem_private_key(
            private_key.encode('utf8'),
            password=None,
            backend=openssl.backend,
        )

    # TODO: if the public key is generated from a private key, maybe we don't
    # want to add a default message
    comment = comment or get_support_email()

    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )
    public_string = '{key} {comment}'.format(
        key=public_bytes.decode('utf8'),
        comment=comment,
    )
    return public_string


def is_valid_private_key(key_text):
    """
    Validate a private key.

    :param key_text: SSH key to validate as text
    :type key_text: str
    :returns: whether or not the private key is valid
    :rtype: bool
    """
    try:
        serialization.load_pem_private_key(
            key_text.encode('utf8'),
            password=None,
            backend=openssl.backend,
        )
        return True
    except (UnicodeEncodeError, ValueError, TypeError):
        return False
