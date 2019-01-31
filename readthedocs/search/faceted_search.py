import logging

from elasticsearch_dsl import FacetedSearch, TermsFacet
from elasticsearch_dsl.query import SimpleQueryString, Bool

from readthedocs.search.documents import PageDocument, ProjectDocument, DomainDocument
from readthedocs.search.signals import before_file_search, before_project_search, before_domain_search


log = logging.getLogger(__name__)


class RTDFacetedSearch(FacetedSearch):

    """Overwrite the initialization in order too meet our needs"""

    # TODO: Remove the overwrite when the elastic/elasticsearch-dsl-py#916
    # See more: https://github.com/elastic/elasticsearch-dsl-py/issues/916

    def __init__(self, user, **kwargs):
        self.user = user
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
        return search


class DomainSearch(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version'),
        'doc_type': TermsFacet(field='doc_type'),
    }
    signal = before_domain_search
    doc_types = [DomainDocument]
    index = DomainDocument._doc_type.index
    fields = ('display_name^5', 'name')


class ProjectSearch(RTDFacetedSearch):
    facets = {
        'language': TermsFacet(field='language')
    }
    signal = before_project_search
    doc_types = [ProjectDocument]
    index = ProjectDocument._doc_type.index
    fields = ('name^10', 'slug^5', 'description')


class PageSearch(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version')
    }
    signal = before_file_search
    doc_types = [PageDocument]
    index = PageDocument._doc_type.index
    fields = ['title^10', 'headers^5', 'content']

    def query(self, search, query):
        """
        Use a custom SimpleQueryString instead of default query
        """

        search = super().query(search, query)

        all_queries = []

        # need to search for both 'and' and 'or' operations
        # the score of and should be higher as it satisfies both or and and
        for operator in ['and', 'or']:
            query_string = SimpleQueryString(query=query, fields=self.fields,
                                             default_operator=operator)
            all_queries.append(query_string)

        # run bool query with should, so it returns result where either of the query matches
        bool_query = Bool(should=all_queries)

        search = search.query(bool_query)
        return search
