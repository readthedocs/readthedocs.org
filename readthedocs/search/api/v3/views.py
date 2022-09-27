import structlog
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView

from readthedocs.projects.models import Feature
from readthedocs.search import tasks
from readthedocs.search.api import SearchPagination
from readthedocs.search.api.v3.backend import Backend
from readthedocs.search.api.v3.serializers import PageSearchSerializer

log = structlog.get_logger(__name__)


class SearchAPI(GenericAPIView):

    """
    Server side search API V3.

    Required query parameters:

    - **q**: Search term.

    Check our [docs](https://docs.readthedocs.io/page/server-side-search.html#api) for more information.
    """  # noqa

    http_method_names = ["get"]
    pagination_class = SearchPagination
    serializer_class = PageSearchSerializer
    search_backend_class = Backend

    def get_view_name(self):
        return "Search API V3"

    def _validate_query_params(self):
        query = self.request.GET.get("q")
        errors = {}
        if not query:
            errors["q"] = [_("This query parameter is required")]
        if errors:
            raise ValidationError(errors)

    @property
    def _backend(self):
        backend = self.search_backend_class(
            request=self.request,
            query=self.request.GET["q"],
        )
        return backend

    def _get_search_query(self):
        return self._backend.parser.query

    def _get_projects_to_search(self):
        return self._backend.projects

    def _use_advanced_query(self):
        # TODO: we should make this a parameter in the API,
        # we are checking if the first project has this feature for now.
        projects = self._get_projects_to_search()
        if projects:
            project = projects[0][0]
            return not project.has_feature(Feature.DEFAULT_TO_FUZZY_SEARCH)
        return True

    def get_queryset(self):
        """
        Returns an Elasticsearch DSL search object or an iterator.

        .. note::

           Calling ``list(search)`` over an DSL search object is the same as
           calling ``search.execute().hits``. This is why an DSL search object
           is compatible with DRF's paginator.
        """
        search = self._backend.search(
            use_advanced_query=self._use_advanced_query(),
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
        serializer = self.get_serializer(
            page, many=True, projects=self._get_projects_to_search()
        )
        response = self.paginator.get_paginated_response(serializer.data)
        response.data["projects"] = [
            [project.slug, version.slug]
            for project, version in self._get_projects_to_search()
        ]
        response.data["query"] = self._get_search_query()
        return response
