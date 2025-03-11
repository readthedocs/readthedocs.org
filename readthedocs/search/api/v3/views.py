from functools import cached_property

import structlog
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle

from readthedocs.api.v3.views import APIv3Settings
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.search import tasks
from readthedocs.search.api.pagination import SearchPagination
from readthedocs.search.api.v3.executor import SearchExecutor
from readthedocs.search.api.v3.serializers import PageSearchSerializer
from readthedocs.search.api.v3.utils import should_use_advanced_query


log = structlog.get_logger(__name__)


RATE_LIMIT = "100/minute"


class SearchAnonRateThrottle(AnonRateThrottle):
    """Rate limit for the search API for anonymous users."""

    rate = RATE_LIMIT


class SearchUserRateThrottle(UserRateThrottle):
    """Rate limit for the search API for authenticated users."""

    rate = RATE_LIMIT


class SearchAPI(APIv3Settings, GenericAPIView):
    """
    Server side search API V3.

    Required query parameters:

    - **q**: [Search term](https://docs.readthedocs.io/page/server-side-search/syntax.html).

    Check our [docs](https://docs.readthedocs.io/page/server-side-search/api.html) for more information.
    """  # noqa

    http_method_names = ["get"]
    pagination_class = SearchPagination
    serializer_class = PageSearchSerializer
    search_executor_class = SearchExecutor
    permission_classes = [AllowAny]
    # The search API would be used by anonymous users,
    # and with our search-as-you-type extension.
    # So we need to increase the rate limit.
    throttle_classes = (SearchUserRateThrottle, SearchAnonRateThrottle)

    @property
    def description(self):
        """
        Get the view description.

        Force the description to always be the docstring of this class,
        even if it's subclassed.
        """
        return SearchAPI.__doc__

    def get_view_name(self):
        return "Search API V3"

    def _validate_query_params(self):
        query = self.request.GET.get("q")
        errors = {}
        if not query:
            errors["q"] = [_("This query parameter is required")]
        if errors:
            raise ValidationError(errors)

    @cached_property
    def _search_executor(self):
        search_executor = self.search_executor_class(
            request=self.request,
            query=self.request.GET["q"],
        )
        return search_executor

    def _get_search_query(self):
        return self._search_executor.parser.query

    def _get_projects_to_search(self):
        return self._search_executor.projects

    def get_queryset(self):
        """
        Returns an Elasticsearch DSL search object or an iterator.

        .. note::

           Calling ``list(search)`` over an DSL search object is the same as
           calling ``search.execute().hits``. This is why an DSL search object
           is compatible with DRF's paginator.
        """
        use_advanced_query = should_use_advanced_query(self._get_projects_to_search())
        search = self._search_executor.search(
            use_advanced_query=use_advanced_query,
            aggregate_results=False,
        )
        if not search:
            return []

        return search

    def get(self, request, *args, **kwargs):
        self._validate_query_params()
        result = self.list()
        self._record_query(result)
        return result

    def _record_query(self, response):
        total_results = response.data.get("count", 0)
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
        queryset = self.get_queryset()
        page = self.paginator.paginate_queryset(
            queryset,
            self.request,
            view=self,
        )
        serializer = self.get_serializer(page, many=True, projects=self._get_projects_to_search())
        response = self.paginator.get_paginated_response(serializer.data)
        self._add_extra_fields(response)
        return response

    def _add_extra_fields(self, response):
        """
        Add additional fields to the top level response.

        These are fields that aren't part of the serializers,
        and are related to the whole list, rather than each element.
        """
        # Add all projects that were used in the final search.
        response.data["projects"] = [
            {"slug": project.slug, "versions": [{"slug": version.slug}]}
            for project, version in self._get_projects_to_search()
        ]
        # Add the query used in the final search,
        # this doesn't include arguments.
        response.data["query"] = self._get_search_query()


class BaseProxiedSearchAPI(SearchAPI):
    """
    Use a separate class for the proxied version of this view.

    This is so we can override it in .com,
    where we need to make use of our auth backends.
    """


class ProxiedSearchAPI(SettingsOverrideObject):
    _default_class = BaseProxiedSearchAPI
