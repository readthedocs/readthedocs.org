from typing import Any

from rest_framework import serializers

from readthedocs.search.api.v2.serializers import PageSearchSerializer as PageSearchSerializerBase


class PageSearchSerializer(PageSearchSerializerBase):
    """
    Serializer for API V3.

    This is very similar to the serializer from V2,
    with the following changes:

    - ``project`` is an object, not a string.
    - ``version`` is an object, not a string.
    - ``project_alias`` isn't present,
      it is contained in the ``project`` object.
    """

    project = serializers.SerializerMethodField()
    version = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("project_alias")

    def get_project(self, obj):
        return {
            "slug": obj.project,
            "alias": self.get_project_alias(obj),
        }

    def get_version(self, obj):
        return {
            "slug": obj.version,
        }


class ProxiedPageSearchSerializer(PageSearchSerializer):
    """
    Serializer for proxied search results.

    Use the subproject alias in the `slug` field for display purposes,
    while still exposing the original project slug.
    """

    def get_project(self, obj: Any) -> dict[str, str | None]:
        alias = self.get_project_alias(obj)
        slug = obj.project
        return {
            "slug": alias or slug,
            "alias": alias,
            "original_slug": slug,
        }
