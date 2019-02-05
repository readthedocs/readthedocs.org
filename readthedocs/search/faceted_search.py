import logging

from elasticsearch_dsl import FacetedSearch, TermsFacet
from elasticsearch_dsl.query import Bool, SimpleQueryString

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.search.documents import PageDocument, ProjectDocument

log = logging.getLogger(__name__)


class RTDFacetedSearch(FacetedSearch):
    """
    Pass in a user in order to filter search results by privacy.

    .. warning::

        This isn't currently used on the .org,
        but is used on the .com
    """

    def __init__(self, user, **kwargs):
        self.user = user
        super().__init__(**kwargs)

    def search(self):
        """
        Filter out full content on search results.

        This was causing all of the indexed content to be returned, which was
        never used on the client side.
        """
        s = super().search()
        s = s.source(exclude=['content', 'headers'])
        return s

    def query(self, search, query):
        """
        Add query part to ``search`` when needed.

        Also does HTML encoding of results to avoid XSS issues.
        """
        search = super().query(search, query)
        search = search.highlight_options(encoder='html', number_of_fragments=3)
        return search


class ProjectSearchBase(RTDFacetedSearch):
    facets = {'language': TermsFacet(field='language')}
    doc_types = [ProjectDocument]
    index = ProjectDocument._doc_type.index
    fields = ('name^10', 'slug^5', 'description')


class PageSearchBase(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version')
    }
    doc_types = [PageDocument]
    index = PageDocument._doc_type.index
    fields = ['title^10', 'headers^5', 'content']

    def query(self, search, query):
        """Use a custom SimpleQueryString instead of default query."""

        search = super().query(search, query)

        all_queries = []

        # need to search for both 'and' and 'or' operations
        # the score of and should be higher as it satisfies both or and and
        for operator in ['and', 'or']:
            query_string = SimpleQueryString(
                query=query, fields=self.fields, default_operator=operator
            )
            all_queries.append(query_string)

        # run bool query with should, so it returns result where either of the query matches
        bool_query = Bool(should=all_queries)

        search = search.query(bool_query)
        return search


class PageSearch(SettingsOverrideObject):
    """
    Allow this class to be overridden based on CLASS_OVERRIDES setting.

    This is primary used on the .com to adjust how we filter our search queries
    """
    _default_class = PageSearchBase


class ProjectSearch(SettingsOverrideObject):
    """
    Allow this class to be overridden based on CLASS_OVERRIDES setting.

    This is primary used on the .com to adjust how we filter our search queries
    """
    _default_class = ProjectSearchBase
