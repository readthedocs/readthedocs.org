from functools import lru_cache, namedtuple, cached_property
from math import ceil

import structlog
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination

from readthedocs.api.mixins import CDNCacheTagsMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.models import Version
from readthedocs.projects.models import Feature, Project
from readthedocs.search import tasks
from readthedocs.search.faceted_search import PageSearch
from readthedocs.search.query import SearchQueryParser

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


class SearchAPIBase(GenericAPIView):

    http_method_names = ['get']
    pagination_class = SearchPagination

    def _validate_query_params(self):
        """
        Validate all query params that are passed in the request.

        :raises: ValidationError if one of them is missing.
        """
        raise NotImplementedError

    def _get_search_query(self):
        raise NotImplementedError

    def _use_advanced_query(self):
        raise NotImplementedError

    def _record_query(self, response):
        raise NotImplementedError

    def _get_projects_to_search(self):
        raise NotImplementedError

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

        :returns: A dictionary of project slugs mapped to a `VersionData` object.
        """
        projects_data = {
            project.slug: self._get_project_data(project, version)
            for project, version in self._get_projects_to_search()
        }
        return projects_data

    def _get_subprojects(self, project, version_slug=None):
        """
        Get a tuple project/version of all subprojects of `project`.

        If `version_slug` doesn't match a version of the subproject,
        the default version will be used.
        If `version_slug` is None, we will always use the default version.
        """
        projects = []
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
                projects.append((project, version))
        return projects

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

    def _has_permission(self, user, version):
        """
        Check if `user` is authorized to access `version`.

        The queryset from `_get_project_version` already filters public
        projects. This is mainly to be overridden in .com to make use of
        the auth backends in the proxied API.
        """
        return True

    def get_queryset(self):
        """
        Returns an Elasticsearch DSL search object or an iterator.

        .. note::

           Calling ``list(search)`` over an DSL search object is the same as
           calling ``search.execute().hits``. This is why an DSL search object
           is compatible with DRF's paginator.
        """
        projects = {
            project.slug: version.slug
            for project, version in self._get_projects_to_search()
        }
        # Check to avoid searching all projects in case it's empty.
        if not projects:
            log.info('Unable to find a version to search')
            return []

        query = self._get_search_query()
        queryset = PageSearch(
            query=query,
            projects=projects,
            aggregate_results=False,
            use_advanced_query=self._use_advanced_query(),
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

    def list(self):
        """List the results using pagination."""
        queryset = self.get_queryset()
        page = self.paginator.paginate_queryset(
            queryset, self.request, view=self,
        )
        serializer = self.get_serializer(page, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class PageSearchAPIView(CDNCacheTagsMixin, SearchAPIBase):

    """
    Server side search API V3.

    Required query parameters:

    - **q**: Search term.
    - **project**: Project to search.
    - **version**: Version to search.

    Check our [docs](https://docs.readthedocs.io/page/server-side-search.html#api) for more information.
    """  # noqa

    permission_classes = [IsAuthorizedToViewVersion]
    serializer_class = PageSearchSerializer
    project_cache_tag = 'rtd-search'

    @lru_cache(maxsize=1)
    def _get_project(self):
        project_slug = self.request.GET.get('project', None)
        project = get_object_or_404(Project, slug=project_slug)
        return project

    @lru_cache(maxsize=1)
    def _get_version(self):
        version_slug = self.request.GET.get('version', None)
        project = self._get_project()
        version = get_object_or_404(
            project.versions.all(),
            slug=version_slug,
        )
        return version

    def _validate_query_params(self):
        errors = {}
        required_query_params = {'q', 'project', 'version'}
        request_params = set(self.request.query_params.keys())
        missing_params = required_query_params - request_params
        for param in missing_params:
            errors[param] = [_("This query param is required")]
        if errors:
            raise ValidationError(errors)

    @lru_cache(maxsize=1)
    def _get_projects_to_search(self):
        main_version = self._get_version()
        main_project = self._get_project()

        if not self._has_permission(self.request.user, main_version):
            return {}

        projects = [(main_project, main_version)]
        projects.extend(self._get_subprojects(main_project, version_slug=main_version.slug))
        return projects

    def _get_search_query(self):
        return self.request.query_params["q"]

    def _record_query(self, response):
        project_slug = self._get_project().slug
        version_slug = self._get_version().slug
        total_results = response.data.get('count', 0)
        time = timezone.now()

        query = self._get_search_query().lower().strip()

        # Record the query with a celery task
        tasks.record_search_query.delay(
            project_slug,
            version_slug,
            query,
            total_results,
            time.isoformat(),
        )

    def _use_advanced_query(self):
        main_project = self._get_project()
        return not main_project.has_feature(Feature.DEFAULT_TO_FUZZY_SEARCH)


class SearchAPIV3(SearchAPIBase):

    """
    Server side search API V3.

    Required query parameters:

    - **q**: Search term.

    Check our [docs](https://docs.readthedocs.io/page/server-side-search.html#api) for more information.
    """  # noqa

    serializer_class = PageSearchSerializer

    def get_view_name(self):
        return "Search API V3"

    def _validate_query_params(self):
        if "q" not in self.request.query_params:
            raise ValidationError({"q": [_("This query parameter is required")]})

    def _get_search_query(self):
        return self._parser.query

    def _use_advanced_query(self):
        # TODO: we should make this a parameter in the API,
        # we are checking if the first project has this feature for now.
        project = self._get_projects_to_search()[0][0]
        return not project.has_feature(Feature.DEFAULT_TO_FUZZY_SEARCH)

    def _record_query(self, response):
        total_results = response.data.get('count', 0)
        time = timezone.now()
        query = self._get_search_query().lower().strip()
        # NOTE: I think this may be confusing,
        # since the number of results is the total
        # of searching on all projects, this specific project
        # could have had 0 results.
        for project, version in self._get_projects_to_search():
            tasks.record_search_query.delay(
                project.slug,
                version.slug,
                query,
                total_results,
                time.isoformat(),
            )

    @cached_property
    def _parser(self):
        parser = SearchQueryParser(self.request.query_params["q"])
        parser.parse()
        return parser

    @lru_cache(maxsize=1)
    def _get_projects_to_search(self):
        projects = []
        for value in self._parser.arguments["project"]:
            project, version = self._get_project_and_version(value)
            if version and self._has_permission(self.request.user, version):
                projects.append((project, version))
        
        for value in self._parser.arguments['subprojects']:
            project, version = self._get_project_and_version(value)

            # Add the project itself.
            if version and self._has_permission(self.request.user, version):
                projects.append((project, version))

            # If the user didn't provide a version, version_slug will be `None`,
            # and we add all subprojects with their default version,
            # otherwise we will add all projects that match the given version.
            _, version_slug = self._split_project_and_version(value)
            projects.extend(
                self._get_subprojects(
                    project=project,
                    version_slug=version_slug,
                ),
            )

        # Add all projects the user has access to.
        if self._parser.arguments["user"] == "@me":
            for project in Project.objects.for_user(user=self.request.user):
                version = self._get_project_version(
                    project=project,
                    version_slug=project.default_version,
                    include_hidden=False,
                )
                if version and self._has_permission(self.request.user, version):
                    projects.append((project, version))

        return projects

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

    def list(self):
        response = super().list()
        response.data["projects"] = [
            [project.slug, version.slug]
            for project, version in self._get_projects_to_search()
        ]
        response.data["query"] = self._get_search_query()
        return response
