from functools import cached_property
from itertools import islice

from readthedocs.builds.constants import INTERNAL
from readthedocs.projects.models import Project
from readthedocs.search.api.v3.queryparser import SearchQueryParser
from readthedocs.search.faceted_search import PageSearch


class SearchExecutor:
    """
    Parse the query, search, and return the projects used in the search.

    :param arguments_required: If `True` and the user didn't provide
     any arguments in the query, we don't perform the search.
    :param default_all: If `True` and `arguments_required` is `False`
     we search all projects by default, otherwise we search all projects
     the user has access to.
    :param max_projects: The maximum number of projects used in the search.
     This limit is only applied for projects given explicitly,
     not when we default to search all projects.
    """

    def __init__(
        self, *, request, query, arguments_required=True, default_all=False, max_projects=100
    ):
        self.request = request
        self.query = query
        self.arguments_required = arguments_required
        self.default_all = default_all
        self.max_projects = max_projects

    @cached_property
    def projects(self):
        """
        Return all projects used in this search.

        If empty, it will search all projects.

        :returns: A list of tuples (project, version).
        """
        projects = islice(self._get_projects_to_search(), self.max_projects)
        # Make sure we are using just one version per-project,
        # searching multiple versions of the same projects isn't supported yet.
        projects_dict = dict(projects)
        return list(projects_dict.items())

    def search(self, **kwargs):
        """
        Perform the search.

        :param kwargs: All kwargs are passed to the `PageSearch` constructor.
        """
        if not self._has_arguments and self.arguments_required:
            return None

        projects = {project.slug: version.slug for project, version in self.projects}
        # If the search is done without projects, ES will search on all projects.
        # If we don't have projects and the user provided arguments,
        # it means we don't have anything to search on (no results).
        # Or if we don't have projects and we don't allow searching all,
        # we also just return.
        if not projects and (self._has_arguments or not self.default_all):
            return None

        search = PageSearch(
            query=self.parser.query,
            projects=projects,
            **kwargs,
        )
        return search

    def _get_projects_to_search(self):
        """
        Return an iterator of (project, version) used in this search.

        An iterator (yield syntax) is used so we can stop at
        ``self.max_projects``, this way we avoid fetching projects
        that we won't use.
        """
        if not self._has_arguments:
            if self.arguments_required:
                return None
            yield from self._get_default_projects()
            return None

        for value in self.parser.arguments["project"]:
            project, version = self._get_project_and_version(value)
            if version and self._has_permission(self.request, version):
                yield project, version

        for value in self.parser.arguments["subprojects"]:
            project, version = self._get_project_and_version(value)

            # Add the project itself.
            if version and self._has_permission(self.request, version):
                yield project, version

            if project:
                # If the user didn't provide a version, version_slug will be `None`,
                # and we add all subprojects with their default version,
                # otherwise we will add all projects that match the given version.
                _, version_slug = self._split_project_and_version(value)
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
            if version and self._has_permission(self.request, version):
                yield project, version

    def _get_subprojects(self, project, version_slug=None):
        """
        Get a tuple (project, version) of all subprojects of `project`.

        If `version_slug` doesn't match a version of the subproject,
        the default version will be used.
        If `version_slug` is None, we will always use the default version.
        """
        relationships = project.subprojects.select_related("child")
        for relationship in relationships:
            subproject = relationship.child
            # NOTE: Since we already have the superproject relationship,
            # we can set it here to avoid an extra query later
            # when using Project.parent_relationship property.
            # The superproject instannce is also shared among all subprojects.
            subproject._superprojects = [relationship]
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

            if version and self._has_permission(self.request, version):
                yield subproject, version

    def _has_permission(self, request, version):
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
            project.versions(manager=INTERNAL)
            .public(
                user=self.request.user,
                only_built=True,
                include_hidden=include_hidden,
            )
            .filter(slug=version_slug)
            .first()
        )

    @cached_property
    def _has_arguments(self):
        return any(self.parser.arguments.values())

    def _get_default_projects(self):
        if self.default_all:
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
