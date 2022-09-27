from functools import cached_property
from itertools import islice

from readthedocs.builds.models import Version
from readthedocs.projects.models import Project
from readthedocs.search.api.v3.parser import SearchQueryParser
from readthedocs.search.faceted_search import PageSearch


class Backend:

    max_projects = 100

    def __init__(self, *, request, query, allow_search_all=False):
        self.request = request
        self.query = query
        self.allow_search_all = allow_search_all

    @cached_property
    def projects(self):
        return list(islice(self._get_projects_to_search(), self.max_projects))

    def search(self, **kwargs):
        projects = {project.slug: version.slug for project, version in self.projects}
        # If the search is done without projects, ES will search on all projects.
        # If we don't have projects and the user provided arguments,
        # it means we don't have anything to search on (no results).
        # Or if we don't have projects and we don't allow searching all,
        # we also just return.
        if not projects and (self._has_arguments or not self.allow_search_all):
            return None

        queryset = PageSearch(
            query=self.parser.query,
            projects=projects,
            **kwargs,
        )
        return queryset

    def _get_projects_to_search(self):
        if not self._has_arguments:
            return self._get_default_projects()

        for value in self.parser.arguments["project"]:
            project, version = self._get_project_and_version(value)
            if version and self._has_permission(self.request.user, version):
                yield project, version

        for value in self.parser.arguments["subprojects"]:
            project, version = self._get_project_and_version(value)

            # Add the project itself.
            if version and self._has_permission(self.request.user, version):
                yield project, version

            # If the user didn't provide a version, version_slug will be `None`,
            # and we add all subprojects with their default version,
            # otherwise we will add all projects that match the given version.
            _, version_slug = self._split_project_and_version(value)
            if project:
                yield from self._get_subprojects(
                    project=project,
                    version_slug=version_slug,
                )

        # Add all projects the user has access to.
        if self.parser.arguments["user"] == "@me":
            yield from self._get_projects_from_user()

    def _get_projects_from_user(self):
        for project in Project.objects.for_user(user=self.request.user):
            version = self._get_project_version(
                project=project,
                version_slug=project.default_version,
                include_hidden=False,
            )
            if version and self._has_permission(self.request.user, version):
                yield project, version

    def _get_subprojects(self, project, version_slug=None):
        """
        Get a tuple project/version of all subprojects of `project`.

        If `version_slug` doesn't match a version of the subproject,
        the default version will be used.
        If `version_slug` is None, we will always use the default version.
        """
        subprojects = Project.objects.filter(superprojects__parent=project)
        for subproject in subprojects:
            version = None
            if version_slug:
                version = self._get_project_version(
                    project=subproject,
                    version_slug=version_slug,
                    include_hidden=False,
                )

            # Fallback to the default version of the subproject.
            if not version and subproject.default_version:
                version = self._get_project_version(
                    project=subproject,
                    version_slug=subproject.default_version,
                    include_hidden=False,
                )

            if version and self._has_permission(self.request.user, version):
                yield project, version

    def _has_permission(self, user, version):
        """
        Check if `user` is authorized to access `version`.

        The queryset from `_get_project_version` already filters public
        projects. This is mainly to be overridden in .com to make use of
        the auth backends in the proxied API.
        """
        return True

    def _get_project_version(self, project, version_slug, include_hidden=True):
        """
        Get a version from a given project.

        :param project: A `Project` object.
        :param version_slug: The version slug.
        :param include_hidden: If hidden versions should be considered.
        """
        return (
            Version.internal.public(
                user=self.request.user,
                project=project,
                only_built=True,
                include_hidden=include_hidden,
            )
            .filter(slug=version_slug)
            .first()
        )

    @property
    def _has_arguments(self):
        return any(self.parser.arguments.values())

    def _get_default_projects(self):
        if self.allow_search_all:
            # Default to search all.
            return []
        return self._get_projects_from_user()

    @cached_property
    def parser(self):
        parser = SearchQueryParser(self.query)
        parser.parse()
        return parser

    def _split_project_and_version(self, term):
        """
        Split a term of the form ``{project}/{version}``.

        :returns: A tuple of project and version.
         If the version part isn't found, `None` will be returned in its place.
        """
        parts = term.split("/", maxsplit=1)
        if len(parts) > 1:
            return parts
        return parts[0], None

    def _get_project_and_version(self, value):
        project_slug, version_slug = self._split_project_and_version(value)
        project = Project.objects.filter(slug=project_slug).first()
        if not project:
            return None, None

        if not version_slug:
            version_slug = project.default_version

        if version_slug:
            version = self._get_project_version(
                project=project,
                version_slug=version_slug,
            )
            return project, version

        return None, None
