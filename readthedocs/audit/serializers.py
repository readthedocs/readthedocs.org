"""Serializers used to save the corresponding data from a model in a log entry."""
from django.contrib.auth.models import User
from rest_framework import serializers

from readthedocs.invitations.models import Invitation
from readthedocs.organizations.models import Organization, Team
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

    # pylint: disable=no-self-use
    def get_object(self, obj):
        if obj.object_type == "organization":
            return OrganizationSerializer(obj.object).data
        if obj.object_type == "project":
            return ProjectSerializer(obj.object).data
        if obj.object_type == "team":
            return TeamSerializer(obj.object).data

        raise ValueError
