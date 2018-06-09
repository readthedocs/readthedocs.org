from elasticsearch_dsl import FacetedSearch, TermsFacet


class ProjectSearch(FacetedSearch):
    fields = ['name^5', 'description']
    facets = {
        'language': TermsFacet(field='language')
    }

    def __init__(self, using, index, doc_types, model, **kwargs):
        self.using = using
        self.index = index
        self.doc_types = doc_types
        self._model = model
        super(ProjectSearch, self).__init__(**kwargs)
