"""
Serializers for the ES's search result object.

.. note::
   Some fields are re-named to make their meaning more clear.
   They should be renamed in the ES index too.
"""

import itertools
import re
from functools import namedtuple
from operator import attrgetter
from urllib.parse import urlparse

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from readthedocs.core.resolver import resolve
from readthedocs.projects.constants import MKDOCS, SPHINX_HTMLDIR
from readthedocs.projects.models import Project


# Structure used for storing cached data of a version mostly.
ProjectData = namedtuple('ProjectData', ['version', 'alias'])
VersionData = namedtuple('VersionData', ['slug', 'docs_url', 'doctype'])


class ProjectHighlightSerializer(serializers.Serializer):

    name = serializers.ListField(child=serializers.CharField(), default=list)
    slug = serializers.ListField(child=serializers.CharField(), default=list)
    description = serializers.ListField(child=serializers.CharField(), default=list)


class ProjectSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='project', source=None, read_only=True)
    name = serializers.CharField()
    slug = serializers.CharField()
    link = serializers.CharField(source='url')
    description = serializers.CharField()
    highlights = ProjectHighlightSerializer(source='meta.highlight', default=dict)


class PageHighlightSerializer(serializers.Serializer):

    title = serializers.ListField(child=serializers.CharField(), default=list)


class PageSearchSerializer(serializers.Serializer):

    """
    Page serializer.

    If ``projects_data`` is passed into the context, the serializer
    will try to use that to generate the link before querying the database.
    It's a dictionary mapping the project slug to a ProjectData object.
    """

    type = serializers.CharField(default='page', source=None, read_only=True)
    project = serializers.CharField()
    project_alias = serializers.SerializerMethodField()
    version = serializers.CharField()
    title = serializers.CharField()
    path = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    highlights = PageHighlightSerializer(source='meta.highlight', default=dict)
    blocks = serializers.SerializerMethodField()

    def _get_project_data(self, obj):
        """
        Get and cache the project data.

        Try to get the data from the ``projects_data`` context,
        and fallback to get it from the database.
        If the result is fetched from the database,
        it's cached into ``projects_data``.
        """
        project_data = self.context.get('projects_data', {}).get(obj.project)
        if project_data:
            return project_data

        project = Project.objects.filter(slug=obj.project).first()
        if project:
            docs_url = project.get_docs_url(version_slug=obj.version)
            project_alias = project.superprojects.values_list('alias', flat=True).first()

            projects_data = self.context.setdefault('projects_data', {})
            version_data = VersionData(
                slug=obj.version,
                docs_url=docs_url,
                doctype=None,
            )
            projects_data[obj.project] = ProjectData(
                alias=project_alias,
                version=version_data,
            )
            return projects_data[obj.project]
        return None

    def get_project_alias(self, obj):
        project_data = self._get_project_data(obj)
        if project_data:
            return project_data.alias
        return None

    def get_domain(self, obj):
        full_path = self._get_full_path(obj)
        if full_path:
            parsed = urlparse(full_path)
            return f'{parsed.scheme}://{parsed.netloc}'
        return None

    def get_path(self, obj):
        full_path = self._get_full_path(obj)
        if full_path:
            parsed = urlparse(full_path)
            return parsed.path
        return None

    def _get_full_path(self, obj):
        project_data = self._get_project_data(obj)
        if project_data:
            docs_url = project_data.version.docs_url
            path = obj.full_path

            # Generate an appropriate link for the doctypes that use htmldir,
            # and always end it with / so it goes directly to proxito.
            if project_data.version.doctype in {SPHINX_HTMLDIR, MKDOCS}:
                path = re.sub('(^|/)index.html$', '/', path)

            return docs_url.rstrip('/') + '/' + path.lstrip('/')
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
            key=attrgetter('meta.score'),
            reverse=True,
        )
        sorted_results = [
            serializers[hit.type](hit).data
            for hit in sorted_results
        ]
        return sorted_results


class DomainHighlightSerializer(serializers.Serializer):

    name = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    def get_name(self, obj):
        name = getattr(obj, 'domains.name', [])
        return list(name)

    def get_content(self, obj):
        docstring = getattr(obj, 'domains.docstrings', [])
        return list(docstring)


class DomainSearchSerializer(serializers.Serializer):

    type = serializers.CharField(default='domain', source=None, read_only=True)
    role = serializers.CharField(source='role_name')
    name = serializers.CharField()
    id = serializers.CharField(source='anchor')
    content = serializers.CharField(source='docstrings')
    highlights = DomainHighlightSerializer(source='meta.highlight', default=dict)


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
    id = serializers.CharField()
    title = serializers.CharField()
    content = serializers.CharField()
    highlights = SectionHighlightSerializer(source='meta.highlight', default=dict)
