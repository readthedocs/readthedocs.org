import logging
from functools import lru_cache, namedtuple
from math import ceil

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext as _
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination

from readthedocs.api.v2.mixins import CachedResponseMixin
from readthedocs.api.v2.permissions import IsAuthorizedToViewVersion
from readthedocs.builds.models import Version
from readthedocs.projects.models import Feature, Project
from readthedocs.search import tasks
from readthedocs.search.faceted_search import PageSearch

from .serializers import PageSearchSerializer, ProjectData, VersionData

log = logging.getLogger(__name__)


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

        total_count = 0
        total_pages = 1
        if queryset:
            total_count = queryset.total_count()
            hits = max(1, total_count)
            total_pages = ceil(hits / page_size)

        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = total_pages

        original_page_number = page_number
        page_number = self._get_page_number(page_number)
        if page_number <= 0:
            msg = self.invalid_page_message.format(
                page_number=original_page_number,
                message=_("Invalid page"),
            )
            raise NotFound(msg)

        if total_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        start = (page_number - 1) * page_size
        end = page_number * page_size
        result = list(queryset[start:end])

        # Needed for other methods of this class.
        self.page = PaginatorPage(
            page_number=page_number,
            total_pages=total_pages,
            count=total_count,
        )

        return result


class PageSearchAPIView(CachedResponseMixin, GenericAPIView):

    """
    Main entry point to perform a search using Elasticsearch.

    Required query params:

    - q (search term)
    - project
    - version

    .. note::

       The methods `_get_project` and `_get_version`
       are called many times, so a basic cache is implemented.
    """

    http_method_names = ['get']
    permission_classes = [IsAuthorizedToViewVersion]
    pagination_class = SearchPagination
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
        """
        Validate all required query params are passed on the request.

        Query params required are: ``q``, ``project`` and ``version``.

        :rtype: None

        :raises: ValidationError if one of them is missing.
        """
        errors = {}
        required_query_params = {'q', 'project', 'version'}
        request_params = set(self.request.query_params.keys())
        missing_params = required_query_params - request_params
        for param in missing_params:
            errors[param] = [_("This query param is required")]
        if errors:
            raise ValidationError(errors)

    @lru_cache(maxsize=1)
    def _get_all_projects_data(self):
        """
        Return a dictionary of the project itself and all its subprojects.

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
        main_version = self._get_version()
        main_project = self._get_project()

        projects_data = {
            main_project.slug: ProjectData(
                alias=None,
                version=VersionData(
                    slug=main_version.slug,
                    docs_url=main_project.get_docs_url(version_slug=main_version.slug),
                ),
            )
        }

        subprojects = Project.objects.filter(
            superprojects__parent_id=main_project.id,
        )
        for subproject in subprojects:
            version = self._get_subproject_version(
                version_slug=main_version.slug,
                subproject=subproject,
            )

            # Fallback to the default version of the subproject.
            if (
                not version
                and main_project.has_feature(Feature.SEARCH_SUBPROJECTS_ON_DEFAULT_VERSION)
                and subproject.default_version
            ):
                version = self._get_subproject_version(
                    version_slug=subproject.default_version,
                    subproject=subproject,
                )

            if version and self._has_permission(self.request.user, version):
                url = subproject.get_docs_url(version_slug=version.slug)
                project_alias = subproject.superprojects.values_list('alias', flat=True).first()
                version_data = VersionData(
                    slug=version.slug,
                    docs_url=url,
                )
                projects_data[subproject.slug] = ProjectData(
                    alias=project_alias,
                    version=version_data,
                )

        return projects_data

    def _get_subproject_version(self, version_slug, subproject):
        """Get a version from the subproject."""
        return (
            Version.internal
            .public(
                user=self.request.user,
                project=subproject,
                include_hidden=False,
                only_built=True,
            )
            .filter(slug=version_slug)
            .first()
        )

    def _has_permission(self, user, version):
        """
        Check if `user` is authorized to access `version`.

        The queryset from `_get_subproject_version` already filters public
        projects. This is mainly to be overriden in .com to make use of
        the auth backends in the proxied API.
        """
        return True

    def _record_query(self, response):
        project_slug = self._get_project().slug
        version_slug = self._get_version().slug
        total_results = response.data.get('count', 0)
        time = timezone.now()

        query = self.request.query_params['q']
        query = query.lower().strip()

        # Record the query with a celery task
        tasks.record_search_query.delay(
            project_slug,
            version_slug,
            query,
            total_results,
            time.isoformat(),
        )

    def get_queryset(self):
        """
        Returns an Elasticsearch DSL search object or an iterator.

        .. note::

           Calling ``list(search)`` over an DSL search object is the same as
           calling ``search.execute().hits``. This is why an DSL search object
           is compatible with DRF's paginator.
        """
        main_project = self._get_project()
        main_version = self._get_version()
        projects = {}
        filters = {}

        if main_project.has_feature(Feature.SEARCH_SUBPROJECTS_ON_DEFAULT_VERSION):
            projects = {
                project: project_data.version.slug
                for project, project_data in self._get_all_projects_data().items()
            }
            # Check to avoid searching all projects in case it's empty.
            if not projects:
                log.info('Unable to find a version to search')
                return []
        else:
            filters['project'] = list(self._get_all_projects_data().keys())
            filters['version'] = main_version.slug
            # Check to avoid searching all projects in case these filters are empty.
            if not filters['project']:
                log.info('Unable to find a project to search')
                return []
            if not filters['version']:
                log.info('Unable to find a version to search')
                return []

        query = self.request.query_params['q']
        queryset = PageSearch(
            query=query,
            projects=projects,
            filters=filters,
            user=self.request.user,
            # We use a permission class to control authorization
            filter_by_user=False,
            use_advanced_query=not main_project.has_feature(Feature.DEFAULT_TO_FUZZY_SEARCH),
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
