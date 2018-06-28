from rest_framework import generics

from readthedocs.search.documents import PageDocument
from readthedocs.search.filters import SearchFilterBackend
from readthedocs.search.pagination import SearchPagination
from readthedocs.search.serializers import PageSearchSerializer


class PageSearchAPIView(generics.ListAPIView):
    pagination_class = SearchPagination
    filter_backends = [SearchFilterBackend]
    serializer_class = PageSearchSerializer

    def get_queryset(self):
        """Return Elasticsearch DSL Search object instead of Django Queryset.

        Django Queryset and elasticsearch-dsl ``Search`` object is similar pattern.
        So for searching, its possible to return ``Search`` object instead of queryset.
        The ``filter_backends`` and ``pagination_class`` is compatible with ``Search``
        """
        query = self.request.query_params.get('query', '')
        queryset = PageDocument.search(query=query)
        return queryset
