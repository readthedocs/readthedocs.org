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
from readthedocs.search.backends import BackendV1, BackendV2

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
    search_backend = None

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

    def get_queryset(self):
        """
        Returns an Elasticsearch DSL search object or an iterator.

        .. note::

           Calling ``list(search)`` over an DSL search object is the same as
           calling ``search.execute().hits``. This is why an DSL search object
           is compatible with DRF's paginator.
        """
        backend = self.search_backend()
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


class ProjectsToSearchMixin:

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


class SearchAPIV3(SearchAPIBase, ProjectsToSearchMixin):

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

    def list(self):
        response = super().list()
        response.data["projects"] = [
            [project.slug, version.slug]
            for project, version in self._get_projects_to_search()
        ]
        response.data["query"] = self._get_search_query()
        return response
