from rest_framework import serializers, viewsets

from readthedocs.core.resolver import resolve
from .models import DomainData


class DomainDataSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    version = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    doc_type = serializers.SerializerMethodField()
    doc_url = serializers.SerializerMethodField()

    class Meta:
        model = DomainData
        fields = ('project', 'version', 'name', 'display_name', 'doc_type', 'doc_url')

    def get_doc_type(self, obj):
        return f'{obj.domain}:{obj.type}'

    def get_doc_url(self, obj):
        path = f'{obj.doc_name}#{obj.anchor}'
        full_url = resolve(project=obj.project, version_slug=obj.version.slug, filename=path)
        return full_url


class DomainDataAPIView(viewsets.ModelViewSet):
    queryset = DomainData.objects.public()
    serializer_class = DomainDataSerializer
    filter_fields = ('project__slug', 'version__slug', 'domain', 'type', 'doc_name', 'name')
