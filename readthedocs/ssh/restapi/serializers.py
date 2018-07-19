# -*- coding: utf-8 -*-
"""Serializers for SSH rest API application."""

from rest_framework import serializers
from ..models import SSHKey


class SSHKeySerializer(serializers.ModelSerializer):

    class Meta(object):
        model = SSHKey
        fields = (
            'id',
            'create_date',
            'public_key',
        )


class SSHKeyAdminSerializer(SSHKeySerializer):

    """
    SSHKey serializer for admin only access.

    Includes the ``private_key`` as main difference.
    """

    class Meta(SSHKeySerializer.Meta):
        fields = SSHKeySerializer.Meta.fields + (
            'private_key',
        )
