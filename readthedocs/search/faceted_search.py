import logging

from elasticsearch_dsl import FacetedSearch, TermsFacet
from readthedocs.search.signals import before_file_search, before_project_search

log = logging.getLogger(__name__)


class RTDFacetedSearch(FacetedSearch):

    """Overwrite the initialization in order too meet our needs"""

    # TODO: Remove the overwrite when the elastic/elasticsearch-dsl-py#916
    # See more: https://github.com/elastic/elasticsearch-dsl-py/issues/916

    def __init__(self, user, using, index, doc_types, model, fields=None, **kwargs):
        self.user = user
        self.using = using
        self.index = index
        self.doc_types = doc_types
        self._model = model
        if fields:
            self.fields = fields
        super(RTDFacetedSearch, self).__init__(**kwargs)

    def search(self):
        """
        Filter out full content on search results

        This was causing all of the indexed content to be returned,
        which was never used on the client side.
        """
        s = super().search()
        s = s.source(exclude=['content', 'headers'])
        resp = self.signal.send(sender=self, user=self.user, search=s)
        if resp:
            # Signal return a search object
            try:
                s = resp[0][1]
            except AttributeError:
                log.exception('Failed to return a search object from search signals')
        return s

    def query(self, search, query):
        """
        Add query part to ``search`` when needed

        Also does HTML encoding of results to avoid XSS issues.

        """
        search = super().query(search, query)
        search = search.highlight_options(encoder='html', number_of_fragments=3)
        if not isinstance(query, str):
            search = search.query(query)
        return search


class ProjectSearch(RTDFacetedSearch):
    facets = {
        'language': TermsFacet(field='language')
    }
    signal = before_project_search


class FileSearch(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version')
    }
    signal = before_file_search
