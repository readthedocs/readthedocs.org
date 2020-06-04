"""
Serializers for the ES's search result object.

.. note::
   Some fields are re-named to make their meaning more clear.
   They should be renamed in the ES index too.
"""

import itertools
from operator import attrgetter

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from readthedocs.core.resolver import resolve
from readthedocs.projects.models import Project


class ProjectHighlightSerializer(serializers.Serializer):

    name = serializers.ListField(child=serializers.CharField(), default=list)
    slug = serializers.ListField(child=serializers.CharField(), default=list)
    description = serializers.ListField(child=serializers.CharField(), default=list)


class ProjectSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='project', source=None, read_only=True)
    name = serializers.CharField()
    slug = serializers.CharField()
    link = serializers.CharField(source='url')
    highlight = ProjectHighlightSerializer(source='meta.highlight', default=dict)


class PageHighlightSerializer(serializers.Serializer):

    title = serializers.ListField(child=serializers.CharField(), default=list)


class PageSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='page', source=None, read_only=True)
    project = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    path = serializers.CharField(source='full_path')
    link = serializers.SerializerMethodField()
    highlight = PageHighlightSerializer(source='meta.highlight', default=dict)
    inner_hits = serializers.SerializerMethodField()

    def get_link(self, obj):
        # TODO: optimize this to not query the db for each result.
        project = Project.objects.filter(slug=obj.project).first()
        if project:
            return resolve(
                project=project,
                version_slug=obj.version,
                filename=obj.full_path,
            )
        return None

    def get_inner_hits(self, obj):
        """Combine and sort inner results (domains and sections)."""
        serializers = {
            'domain': DomainSearchSerializer,
            'section': SectionSearchSerializer,
        }

        inner_hits = obj.meta.inner_hits
        sections = inner_hits.sections or []
        domains = inner_hits.domains or []

        # Make them identifiable before merging them
        for s in sections:
            s.type = 'section'
        for d in domains:
            d.type = 'domain'

        sorted_results = sorted(
            itertools.chain(sections, domains),
            key=attrgetter('_score'),
            reverse=True,
        )
        sorted_results = [
            serializers[hit.type](hit).data
            for hit in sorted_results
        ]
        return sorted_results


class DomainHighlightSerializer(serializers.Serializer):

    """
    Serializer for domain results.

    .. note::

       We override the `to_representation` method instead of declaring each field
       becuase serializers don't play nice with keys that include `.`.
    """

    def to_representation(self, instance):
        return {
            'name': getattr(instance, 'domains.name', []),
            'docstring': getattr(instance, 'domains.docstrings', []),
        }


class DomainSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='domain', source=None, read_only=True)
    role_name = serializers.CharField(source='_source.role_name')
    name = serializers.CharField(source='_source.name')
    id = serializers.CharField(source='_source.anchor')
    docstring = serializers.CharField(source='_source.docstrings')
    highlight = DomainHighlightSerializer(default=dict)


class SectionHighlightSerializer(serializers.Serializer):

    """
    Serializer for section results.

    .. note::

       We override the `to_representation` method instead of declaring each field
       becuase serializers don't play nice with keys that include `.`.
    """

    def to_representation(self, instance):
        return {
            'title': getattr(instance, 'sections.title', []),
            'content': getattr(instance, 'sections.content', []),
        }


class SectionSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='section', source=None, read_only=True)
    id = serializers.CharField(source='_source.id')
    title = serializers.CharField(source='_source.title')
    content = serializers.CharField(source='_source.content')
    highlight = SectionHighlightSerializer(default=dict)
