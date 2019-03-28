"""Domain API classes."""

from rest_framework import serializers

from readthedocs.restapi.views.model_views import UserSelectViewSet

from .models import SphinxDomain


class SphinxDomainSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    version = serializers.SlugRelatedField(slug_field='slug', read_only=True)

    class Meta:
        model = SphinxDomain
        fields = (
            'project',
            'version',
            'name',
            'display_name',
            'role_name',
            'docs_url',
        )


class SphinxDomainAdminSerializer(SphinxDomainSerializer):

    class Meta(SphinxDomainSerializer.Meta):
        fields = '__all__'


class SphinxDomainAPIView(UserSelectViewSet):  # pylint: disable=too-many-ancestors
    model = SphinxDomain
    serializer_class = SphinxDomainSerializer
    admin_serializer_class = SphinxDomainAdminSerializer
    filterset_fields = (
        'project__slug',
        'version__slug',
        'domain',
        'type',
        'doc_name',
        'name',
    )
