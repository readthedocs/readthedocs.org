from functools import lru_cache, namedtuple
from math import ceil

import structlog
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.builds.models import Version
from readthedocs.core.utils import get_cache_tag
from readthedocs.projects.models import Feature, Project
from readthedocs.search import tasks
from readthedocs.search.faceted_search import PageSearch

from .serializers import PageSearchSerializer, ProjectData, VersionData

log = structlog.get_logger(__name__)


class PaginatorPage:

    """
    Mimics the result from a paginator.

    By using this class, we avoid having to override a lot of methods
    of `PageNumberPagination` to make it work with the ES DSL object.
    """

    def __init__(self, page_number, total_pages, count):
        self.number = page_number
        Paginator = namedtuple('Paginator', ['num_pages', 'count'])
        self.paginator = Paginator(total_pages, count)

    def has_next(self):
        return self.number < self.paginator.num_pages

    def has_previous(self):
        return self.number > 1

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1


class SearchPagination(PageNumberPagination):

    """Paginator for the results of PageSearch."""

    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

    def _get_page_number(self, number):
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            number = -1
        return number

    def paginate_queryset(self, queryset, request, view=None):
        """
        Override to get the paginated result from the ES queryset.

        This makes use of our custom paginator and slicing support from the ES DSL object,
        instead of the one used by django's ORM.

        Mostly inspired by https://github.com/encode/django-rest-framework/blob/acbd9d8222e763c7f9c7dc2de23c430c702e06d4/rest_framework/pagination.py#L191  # noqa
        """
        # Needed for other methods of this class.
        self.request = request

        page_size = self.get_page_size(request)
        page_number = request.query_params.get(self.page_query_param, 1)

        original_page_number = page_number
        page_number = self._get_page_number(page_number)

        if page_number <= 0:
            msg = self.invalid_page_message.format(
                page_number=original_page_number,
                message=_("Invalid page"),
            )
            raise NotFound(msg)

        start = (page_number - 1) * page_size
        end = page_number * page_size

        result = []
        total_count = 0
        total_pages = 1

        if queryset:
            result = queryset[start:end].execute()
            total_count = result.hits.total['value']
            hits = max(1, total_count)
            total_pages = ceil(hits / page_size)

        if total_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        # Needed for other methods of this class.
        self.page = PaginatorPage(
            page_number=page_number,
            total_pages=total_pages,
            count=total_count,
        )

        return result


class PageSearchAPIView(CDNCacheTagsMixin, GenericAPIView):

    """
    Server side search API.

    Required query params:

    - **q**: Search term
    - **project**: List of projects to search, they can be in the form
      of `{project}` or `{project}:{version}`.
      If no version is passed, its default version is used.
    - **version** (deprecated): Use the `project` parameter with the
      `{project}:{version}` syntax instead.

    Check our [docs](https://docs.readthedocs.io/en/stable/server-side-search.html#api) for more information.
    """  # noqa

    http_method_names = ['get']
    # Access is decided while listing results from a version.
    # If a user doesn't have access to a version,
    # we just don't include results from that version
    # instead of returning an error.
    permission_classes = []
    pagination_class = SearchPagination
    serializer_class = PageSearchSerializer
    project_cache_tag = "rtd-search"

    @lru_cache(maxsize=1)
    def _get_project(self):
        """
        Get the current project (deprecated).

        This method is deprecated, the request
        could be attached to more than one project.
        """
        project_slug = self.request.GET.get('project', None)
        project = get_object_or_404(Project, slug=project_slug)
        return project

    @lru_cache(maxsize=1)
    def _get_version(self):
        """
        Get the current version (deprecated).

        This method is deprecated, the request
        could be attached to more than one version.
        """
        project = self._get_project()
        version_slug = self.request.GET.get("version")
        version = get_object_or_404(
            project.versions.all(),
            slug=version_slug,
        )
        return version

    def _validate_query_params(self):
        """
        Validate all query params that are passed in the request.

        Required parameters are: ``q``, and ``project``.
        The query param ``version`` can only be used with one single project.

        :raises: ValidationError
        """
        errors = {}
        required_query_params = ["q", "project"]
        for param in required_query_params:
            param_value = self.request.GET.get(param)
            if not param_value:
                errors[param] = [_("This parameter is required")]

        has_version = self.request.GET.get("version")
        if has_version:
            projects_slug = self.request.GET.getlist("project")
            if len(projects_slug) > 1:
                errors["version"] = [
                    _("The version parameter can't be used with more than one project")
                ]
            if len(projects_slug) == 1:
                __, version_slug = self._split_project_and_version(projects_slug[0])
                if version_slug is not None:
                    errors["project"] = [
                        _(
                            "The `{project}:{version}` syntax can't be used "
                            "with the `version` parameter"
                        )
                    ]

        if errors:
            raise ValidationError(errors)

    @lru_cache(maxsize=1)
    def _get_all_projects_data(self):
        """
        Return a dictionary of all projects/versions that will be used in the search.

        Example:

        .. code::

           {
               "requests": ProjectData(
                   alias='alias',
                   version=VersionData(
                        "latest",
                        "https://requests.readthedocs.io/en/latest/",
                    ),
               ),
               "requests-oauth": ProjectData(
                   alias=None,
                   version=VersionData(
                       "latest",
                       "https://requests-oauth.readthedocs.io/en/latest/",
                   ),
               ),
           }

        .. note:: The response is cached into the instance.

        :rtype: A dictionary of project slugs mapped to a `VersionData` object.
        """
        if self._is_old_request():
            return self._get_single_project_data()
        return self._get_multiple_projects_data()

    def _is_old_request(self):
        """
        Check if the request is using the old API syntax.

        With the old syntax, only one project and version
        are allowed, and results will always include results
        from subprojects.
        """
        return self.request.GET.get("version")

    def _get_single_project_data(self):
        """
        Get project data from a single project (old API syntax).

        This includes the subprojects of the main project
        that have the same version as the main project,
        if there isn't a match, the default version will be used.

        .. note::

           We exlude hidden versions when matching the versions
           from subprojects.
        """
        main_version = self._get_version()
        main_project = self._get_project()

        if not self._has_permission(self.request.user, main_version):
            return {}

        projects_data = {
            main_project.slug: self._get_project_data(main_project, main_version),
        }

        subprojects = Project.objects.filter(superprojects__parent_id=main_project.id)
        for subproject in subprojects:
            version = self._get_project_version(
                project=subproject,
                version_slug=main_version.slug,
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
                projects_data[subproject.slug] = self._get_project_data(
                    subproject, version
                )

        return projects_data

    def _get_multiple_projects_data(self):
        """
        Get project data from all projects/versions the current user has access to.

        No additional projects/versions from the explicitly requested are added
        (no subprojects).
        """
        projects_slug = self.request.GET.getlist("project")
        projects_data = {}
        for project_slug in projects_slug:
            project_slug, version_slug = self._split_project_and_version(project_slug)
            project = Project.objects.filter(slug=project_slug).first()
            if not project:
                continue

            if not version_slug and project.default_version:
                version_slug = project.default_version

            version = self._get_project_version(
                project=project,
                version_slug=version_slug,
            )
            if version and self._has_permission(self.request.user, version):
                projects_data[project.slug] = self._get_project_data(project, version)

        return projects_data

    def _get_project_version(self, project, version_slug, include_hidden=True):
        """
        Get a version from a given project.

        :param project: A `Project` object.
        :param version_slug: The version slug.
        :param include_hidden: If hidden versions should be considered.
        """
        return (
            Version.internal
            .public(
                user=self.request.user,
                project=project,
                only_built=True,
                include_hidden=include_hidden,
            )
            .filter(slug=version_slug)
            .first()
        )

    def _split_project_and_version(self, term):
        """
        Split a term of the form ``{project}:{version}``.

        :returns: A tuple of project and version.
         If the version part isn't found, `None` will be returned in its place.
        """
        parts = term.split(":", maxsplit=1)
        if len(parts) > 1:
            return parts
        return parts[0], None

    def _get_project_data(self, project, version):
        """Build a `ProjectData` object given a project and its version."""
        url = project.get_docs_url(version_slug=version.slug)
        project_alias = project.superprojects.values_list("alias", flat=True).first()
        version_data = VersionData(
            slug=version.slug,
            docs_url=url,
        )
        return ProjectData(
            alias=project_alias,
            version=version_data,
        )

    def _has_permission(self, user, version):
        """
        Check if `user` is authorized to access `version`.

        The queryset from `_get_project_version` already filters public
        projects. This is mainly to be overridden in .com to make use of
        the auth backends in the proxied API.
        """
        return True

    def _record_query(self, response):
        """
        Record the current query for analytics.

        We record the same query for every
        project involved in the request.
        """
        total_results = response.data.get('count', 0)
        time = timezone.now()
        query = self.request.query_params['q']
        query = query.lower().strip()
        for project_slug, project_data in self._get_all_projects_data().items():
            tasks.record_search_query.delay(
                project_slug=project_slug,
                version_slug=project_data.version.slug,
                query=query,
                total_results=total_results,
                time_string=time.isoformat(),
            )

    def get_queryset(self):
        """
        Returns an Elasticsearch DSL search object or an iterator.

        .. note::

           Calling ``list(search)`` over an DSL search object is the same as
           calling ``search.execute().hits``. This is why an DSL search object
           is compatible with DRF's paginator.
        """
        projects = {
            project: project_data.version.slug
            for project, project_data in self._get_all_projects_data().items()
        }
        # Check to avoid searching all projects in case it's empty.
        if not projects:
            log.info('Unable to find a version to search')
            return []

        # TODO: we should make this a parameter in the API,
        # we are checking if the first project has this feature for now.
        first_project = next(iter(projects.keys()))
        main_project = Project.objects.get(slug=first_project)
        use_advanced_query = not main_project.has_feature(
            Feature.DEFAULT_TO_FUZZY_SEARCH
        )

        query = self.request.query_params['q']
        queryset = PageSearch(
            query=query,
            projects=projects,
            aggregate_results=False,
            use_advanced_query=use_advanced_query,
        )
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['projects_data'] = self._get_all_projects_data()
        return context

    def get(self, request, *args, **kwargs):
        self._validate_query_params()
        result = self.list()
        self._record_query(result)
        return result

    def _get_cache_tags(self):
        """Overriden from `CDNCacheTagsMixin` to return tags for all projects."""
        try:
            projects_data = self._get_all_projects_data()
        except Http404:
            return []
        tags = []
        for project_slug, project_data in projects_data.items():
            tags.append(project_slug)
            tags.append(get_cache_tag(project_slug, project_data.version.slug))
            tags.append(get_cache_tag(project_slug, self.project_cache_tag))
        return tags

    def list(self):
        """List the results using pagination."""
        queryset = self.get_queryset()
        page = self.paginator.paginate_queryset(
            queryset, self.request, view=self,
        )
        serializer = self.get_serializer(page, many=True)
        response = self.paginator.get_paginated_response(serializer.data)
        self._insert_additional_metadata(response)
        return response

    def _insert_additional_metadata(self, response):
        """
        Insert additional metadata about the search.

        Currently, we insert:

        - The final projects and its versions that were used in the search.
        """
        response.data["versions"] = [
            {
                "slug": project_data.version.slug,
                "project": {"slug": project_slug},
            }
            for project_slug, project_data in self._get_all_projects_data().items()
        ]
