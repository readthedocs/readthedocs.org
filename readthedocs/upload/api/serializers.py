from enum import StrEnum

from django.conf import settings
from rest_framework import serializers

from readthedocs.builds.constants import BRANCH
from readthedocs.builds.constants import EXTERNAL
from readthedocs.builds.constants import TAG
from readthedocs.projects.constants import PRIVATE
from readthedocs.projects.constants import PUBLIC


class UploadVersionSerializer(serializers.Serializer):
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
        choices=[PUBLIC, PRIVATE],
        required=False,
        default=PRIVATE,
        help_text="Privacy level for the version.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.ALLOW_PRIVATE_REPOS:
            self.fields["privacy_level"].default = PUBLIC
            self.fields["privacy_level"].choices = [PUBLIC]


class UploadURLSerializer(serializers.Serializer):
    """Serializer for the upload URL and required fields to interact with S3."""

    url = serializers.URLField(
        help_text="URL for uploading the build artifacts.",
    )
    # NOTE: url_fields is used to avoid a conflict with the `fields` attribute of the serializer.
    url_fields = serializers.DictField(
        source="fields",
        help_text="Additional fields required for the upload.",
    )


class UploadInitiateSerializer(serializers.Serializer):
    """Serializer for the upload initiate endpoint."""

    project = serializers.CharField(
        required=True,
        help_text="Project identifier (slug).",
    )
    version = UploadVersionSerializer()


class UploadInitiateResponseSerializer(serializers.Serializer):
    """Response serializer for the upload initiate endpoint."""

    build = serializers.DictField()
    version = serializers.DictField()
    upload_url = UploadURLSerializer()


class UploadStatus(StrEnum):
    succes = "success"
    failed = "failed"


class UploadCompleteSerializer(serializers.Serializer):
    """Serializer for the upload complete endpoint."""

    build = serializers.IntegerField(
        help_text="Build ID returned from the initiate endpoint.",
    )
    status = serializers.ChoiceField(
        choices=[status for status in UploadStatus],
        help_text="Status of the upload after completion.",
    )
