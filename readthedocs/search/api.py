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
        query = self.request.query_params.get('query')
        queryset = PageDocument.search(query=query)
        return queryset
