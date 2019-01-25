from elasticsearch_dsl import FacetedSearch, TermsFacet


class RTDFacetedSearch(FacetedSearch):

    """Overwrite the initialization in order too meet our needs"""

    # TODO: Remove the overwrite when the elastic/elasticsearch-dsl-py#916
    # See more: https://github.com/elastic/elasticsearch-dsl-py/issues/916

    def __init__(self, using, index, doc_types, model, fields=None, **kwargs):
        self.using = using
        self.index = index
        self.doc_types = doc_types
        self._model = model
        if fields:
            self.fields = fields
        super(RTDFacetedSearch, self).__init__(**kwargs)


class ProjectSearch(RTDFacetedSearch):
    fields = ['name^5', 'description']
    facets = {
        'language': TermsFacet(field='language')
    }


class FileSearch(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version')
    }

    def query(self, search, query):
        """
        Add query part to ``search``

        Overriding because we pass ES Query object instead of string
        """
        search = search.highlight_options(encoder='html')
        if query:
            search = search.query(query)

        return search
