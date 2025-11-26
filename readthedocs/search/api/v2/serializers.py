"""
Serializers for the ES's search result object.

.. note::
   Some fields are re-named to make their meaning more clear.
   They should be renamed in the ES index too.
"""

import re
from functools import namedtuple
from urllib.parse import urlparse

from rest_framework import serializers

from readthedocs.builds.models import Version
from readthedocs.core.resolver import Resolver
from readthedocs.projects.constants import GENERIC
from readthedocs.projects.constants import MKDOCS
from readthedocs.projects.constants import SPHINX_HTMLDIR


# Structures used for storing cached data of a version mostly.
ProjectData = namedtuple("ProjectData", ["version", "alias"])
VersionData = namedtuple("VersionData", ["slug", "docs_url"])


class ProjectHighlightSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_name(self, obj):
        return list(getattr(obj, "name", []))

    def get_slug(self, obj):
        return list(getattr(obj, "slug", []))

    def get_description(self, obj):
        return list(getattr(obj, "description", []))


class ProjectSearchSerializer(serializers.Serializer):
    type = serializers.CharField(default="project", source=None, read_only=True)
    name = serializers.CharField()
    slug = serializers.CharField()
    link = serializers.CharField(source="url")
    description = serializers.CharField()
    highlights = ProjectHighlightSerializer(source="meta.highlight", default=dict)


class PageHighlightSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return list(getattr(obj, "title", []))


class SectionHighlightSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    def get_title(self, obj):
        return list(getattr(obj, "sections.title", []))

    def get_content(self, obj):
        return list(getattr(obj, "sections.content", []))


class SectionSearchSerializer(serializers.Serializer):
    type = serializers.CharField(default="section", source=None, read_only=True)
    id = serializers.CharField()
    title = serializers.CharField()
    content = serializers.CharField()
    highlights = SectionHighlightSerializer(source="meta.highlight", default=dict)


class PageSearchSerializer(serializers.Serializer):
    """
    Page serializer.

    If ``projects`` is passed in the constructor, the serializer
    will pre-generate a cache with that information,
    this is to avoid querying the database again for each result.

    :param projects: A list of tuples of project and version.
    """

    type = serializers.CharField(default="page", source=None, read_only=True)
    project = serializers.CharField()
    project_alias = serializers.SerializerMethodField()
    version = serializers.CharField()
    title = serializers.CharField()
    path = serializers.SerializerMethodField()
    domain = serializers.SerializerMethodField()
    highlights = PageHighlightSerializer(source="meta.highlight", default=dict)
    blocks = SectionSearchSerializer(source="meta.inner_hits.sections", many=True, default=list)

    def __init__(self, *args, projects=None, **kwargs):
        if projects:
            context = kwargs.setdefault("context", {})
            context["projects_data"] = {
                project.slug: self._build_project_data(project, version=version)
                for project, version in projects
            }
        super().__init__(*args, **kwargs)

    def _build_project_data(self, project, version):
        """Build a `ProjectData` object given a project and its version."""
        # NOTE: re-using the resolver doesn't help here,
        # as this method is called just once per project,
        # re-using the resolver is useful when resolving the same project multiple times.
        url = Resolver().resolve_version(project, version)
        project_alias = None
        if project.parent_relationship:
            project_alias = project.parent_relationship.alias
        version_data = VersionData(
            slug=version.slug,
            docs_url=url,
        )
        return ProjectData(
            alias=project_alias,
            version=version_data,
        )

    def _get_project_data(self, obj):
        """
        Get and cache the project data.

        Try to get the data from the ``projects_data`` context,
        and fallback to get it from the database.
        If the result is fetched from the database,
        it's cached into ``projects_data``.
        """
        project_data = self.context.get("projects_data", {}).get(obj.project)
        if project_data:
            return project_data

        version = (
            Version.objects.filter(project__slug=obj.project, slug=obj.version)
            .select_related("project")
            .first()
        )
        if version:
            project = version.project
            projects_data = self.context.setdefault("projects_data", {})
            projects_data[obj.project] = self._build_project_data(project, version=version)
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
            return f"{parsed.scheme}://{parsed.netloc}"
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
            # For a generic doctype we just strip the index.html part if it exists.
            if obj.doctype in {SPHINX_HTMLDIR, MKDOCS, GENERIC}:
                path = re.sub("(^|/)index.html$", "/", path)

            return docs_url.rstrip("/") + "/" + path.lstrip("/")
        return None
