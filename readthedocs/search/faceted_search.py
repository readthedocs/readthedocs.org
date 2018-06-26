from elasticsearch_dsl import FacetedSearch, TermsFacet
from elasticsearch_dsl.query import SimpleQueryString, Bool


class RTDFacetedSearch(FacetedSearch):

    """Overwrite the initialization in order too meet our needs"""

    # TODO: Remove the overwrite when the elastic/elasticsearch-dsl-py#916
    # See more: https://github.com/elastic/elasticsearch-dsl-py/issues/916

    def __init__(self, using, index, doc_types, model, **kwargs):
        self.using = using
        self.index = index
        self.doc_types = doc_types
        self._model = model
        super(RTDFacetedSearch, self).__init__(**kwargs)


class ProjectSearch(RTDFacetedSearch):
    fields = ['name^5', 'description']
    facets = {
        'language': TermsFacet(field='language')
    }


class FileSearch(RTDFacetedSearch):
    fields = ['title^10', 'headers^5', 'content']
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version')
    }

    def query(self, search, query):
        """Add query part to ``search``"""
        if query:
            all_queries = []

            # Need to search for both 'AND' and 'OR' operations
            # The score of AND should be higher as it comes first
            for operator in ['AND', 'OR']:
                query_string = SimpleQueryString(query=query, fields=self.fields,
                                                 default_operator=operator)
                all_queries.append(query_string)

            # Run bool query with should, so it returns result where either of the query matches
            bool_query = Bool(should=all_queries)
            search = search.query(bool_query)

        return search
