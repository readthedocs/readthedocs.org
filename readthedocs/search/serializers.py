"""
Serializers for the ES's search result object.

.. note::
   Some fields are re-named to make their meaning more clear.
   They should be renamed in the ES index too.
"""

import itertools
import re
from operator import attrgetter

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from readthedocs.core.resolver import resolve
from readthedocs.projects.constants import MKDOCS, SPHINX_HTMLDIR
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
    highlights = ProjectHighlightSerializer(source='meta.highlight', default=dict)


class PageHighlightSerializer(serializers.Serializer):

    title = serializers.ListField(child=serializers.CharField(), default=list)


class PageSearchSerializer(serializers.Serializer):

    """
    Page serializer.

    If ``projects_data`` is passed into the context, the serializer
    will try to use that to generate the link before querying the database.
    It's a dictionary containing the project slug, and its version URL
    and version's doctype.
    """

    type = serializers.CharField(default='page', source=None, read_only=True)
    project = serializers.CharField()
    version = serializers.CharField()
    title = serializers.CharField()
    link = serializers.SerializerMethodField()
    highlights = PageHighlightSerializer(source='meta.highlight', default=dict)
    blocks = serializers.SerializerMethodField()

    def get_link(self, obj):
        # TODO: return a relative URL when this is called from the indoc search.

        # First try to build the URL from the context.
        project_data = self.context.get('projects_data', {}).get(obj.project)
        if project_data:
            docs_url, doctype = project_data
            path = obj.full_path

            # Generate an appropriate link for the doctypes that use htmldir,
            # and always end it with / so it goes directly to proxito.
            if doctype in {SPHINX_HTMLDIR, MKDOCS}:
                new_path = re.sub('(^|/)index.html$', '/', path)
                # docs_url already ends with /,
                # so path doesn't need to start with /.
                path = new_path.lstrip('/')

            return docs_url + path

        # Fallback to build the URL querying the db.
        project = Project.objects.filter(slug=obj.project).first()
        if project:
            docs_url = project.get_docs_url(version_slug=obj.version)
            # cache the project URL
            projects_data = self.context.setdefault('projects_data', {})
            projects_data[obj.project] = (docs_url, '')
            return docs_url + obj.full_path

        return None

    def get_blocks(self, obj):
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

    name = serializers.SerializerMethodField()
    docstring = serializers.SerializerMethodField()

    def get_name(self, obj):
        name = getattr(obj, 'domains.name', [])
        return list(name)

    def get_docstring(self, obj):
        docstring = getattr(obj, 'domains.docstrings', [])
        return list(docstring)


class DomainSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='domain', source=None, read_only=True)
    role = serializers.CharField(source='_source.role_name')
    name = serializers.CharField(source='_source.name')
    id = serializers.CharField(source='_source.anchor')
    docstring = serializers.CharField(source='_source.docstrings')
    highlights = DomainHighlightSerializer(source='highlight', default=dict)


class SectionHighlightSerializer(serializers.Serializer):

    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    def get_title(self, obj):
        title = getattr(obj, 'sections.title', [])
        return list(title)

    def get_content(self, obj):
        content = getattr(obj, 'sections.content', [])
        return list(content)


class SectionSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='section', source=None, read_only=True)
    id = serializers.CharField(source='_source.id')
    title = serializers.CharField(source='_source.title')
    content = serializers.CharField(source='_source.content')
    highlights = SectionHighlightSerializer(source='highlight', default=dict)
