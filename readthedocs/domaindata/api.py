"""Domain API classes."""

from rest_framework import serializers

from readthedocs.restapi.views.model_views import UserSelectViewSet

from .models import DomainData


class DomainDataSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    version = serializers.SlugRelatedField(slug_field='slug', read_only=True)

    class Meta:
        model = DomainData
        fields = (
            'project',
            'version',
            'name',
            'display_name',
            'doc_type',
            'doc_url',
        )


class DomainDataAdminSerializer(DomainDataSerializer):

    class Meta(DomainDataSerializer.Meta):
        fields = '__all__'


class DomainDataAPIView(UserSelectViewSet):  # pylint: disable=too-many-ancestors
    model = DomainData
    serializer_class = DomainDataSerializer
    admin_serializer_class = DomainDataAdminSerializer
    filter_fields = (
        'project__slug',
        'version__slug',
        'domain',
        'type',
        'doc_name',
        'name',
    )
