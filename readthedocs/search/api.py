from rest_framework import generics
from rest_framework import exceptions
from rest_framework.exceptions import ValidationError

from readthedocs.search.documents import PageDocument
from readthedocs.search.filters import SearchFilterBackend
from readthedocs.search.pagination import SearchPagination
from readthedocs.search.serializers import PageSearchSerializer


class PageSearchAPIView(generics.ListAPIView):
    pagination_class = SearchPagination
    filter_backends = [SearchFilterBackend]
    serializer_class = PageSearchSerializer

    def get_queryset(self):
        """
        Return Elasticsearch DSL Search object instead of Django Queryset.

        Django Queryset and elasticsearch-dsl ``Search`` object is similar pattern.
        So for searching, its possible to return ``Search`` object instead of queryset.
        The ``filter_backends`` and ``pagination_class`` is compatible with ``Search``
        """
        # Validate all the required params are there
        self.validate_query_params()
        query = self.request.query_params.get('query', '')
        queryset = PageDocument.simple_search(query=query)
        return queryset

    def validate_query_params(self):
        required_query_params = {'query', 'project', 'version'}  # python `set` literal is `{}`
        request_params = set(self.request.query_params.keys())
        missing_params = required_query_params - request_params
        if missing_params:
            errors = {}
            for param in missing_params:
                errors[param] = ["This query param is required"]

            raise ValidationError(errors)
