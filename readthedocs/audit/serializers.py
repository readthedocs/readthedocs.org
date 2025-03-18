"""
Serializers used to save the corresponding data from a model in a log entry.

.. note::

   These aren't used in an API, but to extract data from objects to
   save it in log entries (AuditLog.data).
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization
from readthedocs.organizations.models import Team
from readthedocs.projects.models import Project


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "slug"]


class TeamSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = Team
        fields = ["id", "slug", "organization"]


class ProjectSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = Project
        fields = ["id", "slug", "organization"]


class InvitationSerializer(serializers.ModelSerializer):
    """Invitation serializer."""

    to_user = UserSerializer()
    from_user = UserSerializer()
    object = serializers.SerializerMethodField()

    class Meta:
        model = Invitation
        fields = [
            "id",
            "from_user",
            "to_user",
            "to_email",
            "object_type",
            "object",
            "from_user",
        ]

    def get_object(self, obj):
        # The type of obj depends on the invitation,
        # a different serializer is used for each type.
        obj_serializers = {
            "organization": OrganizationSerializer,
            "project": ProjectSerializer,
            "team": TeamSerializer,
        }
        serializer = obj_serializers[obj.object_type]
        return serializer(obj.object).data
