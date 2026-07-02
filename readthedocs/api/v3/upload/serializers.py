from django.conf import settings
from rest_framework import serializers

from readthedocs.builds.constants import BRANCH, EXTERNAL, TAG


class VersionMetadataSerializer(serializers.Serializer):
    """Serializer for version metadata in the upload initiate request."""

    name = serializers.CharField(
        help_text="Name of the Git branch/tag or PR number.",
    )
    type = serializers.ChoiceField(
        choices=[BRANCH, TAG, EXTERNAL],
        help_text="Type of version: branch, tag, or external (PR).",
    )
    commit = serializers.CharField(
        max_length=255,
        help_text="Full commit hash.",
    )
    slug = serializers.SlugField(
        required=False,
        allow_blank=True,
        help_text="Optional slug. If not provided, derived from the name.",
    )
    privacy_level = serializers.ChoiceField(
        choices=["public", "private"],
        required=False,
        default=settings.DEFAULT_VERSION_PRIVACY_LEVEL,
        help_text="Privacy level for the version.",
    )


class UploadInitiateSerializer(serializers.Serializer):
    """Serializer for the upload initiate endpoint."""

    project = serializers.SlugField(
        required=False,
        help_text="Project slug. Required if token is not project-scoped.",
    )
    version = VersionMetadataSerializer()


class UploadInitiateResponseSerializer(serializers.Serializer):
    """Response serializer for the upload initiate endpoint."""

    build = serializers.DictField()
    version = serializers.DictField()
    upload_url = serializers.DictField()


class UploadCompleteSerializer(serializers.Serializer):
    """Serializer for the upload complete endpoint."""

    build = serializers.IntegerField(
        help_text="Build ID returned from the initiate endpoint.",
    )
    status = serializers.ChoiceField(
        choices=["uploaded", "failed"],
        help_text="Status of the upload: 'uploaded' or 'failed'.",
    )
