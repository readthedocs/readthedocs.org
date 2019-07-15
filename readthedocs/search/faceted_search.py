import logging

from elasticsearch import Elasticsearch
from elasticsearch_dsl import FacetedSearch, TermsFacet
from elasticsearch_dsl.faceted_search import NestedFacet
from elasticsearch_dsl.query import Bool, SimpleQueryString, Nested, Match

from django.conf import settings

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.search.documents import (
    PageDocument,
    ProjectDocument,
)


log = logging.getLogger(__name__)

ALL_FACETS = ['project', 'version', 'role_name', 'language', 'index']


class RTDFacetedSearch(FacetedSearch):

    def __init__(self, user, **kwargs):
        """
        Pass in a user in order to filter search results by privacy.

        .. warning::

            The `self.user` and `self.filter_by_user` attributes
            aren't currently used on the .org, but are used on the .com.
        """
        self.user = user
        self.filter_by_user = kwargs.pop('filter_by_user', True)

        # Set filters properly
        for facet in self.facets:
            if facet in kwargs:
                kwargs.setdefault('filters', {})[facet] = kwargs.pop(facet)

        # Don't pass along unnecessary filters
        for f in ALL_FACETS:
            if f in kwargs:
                del kwargs[f]

        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.info('Hacking Elastic to fix search connection pooling')
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])

        super().__init__(**kwargs)

    def query(self, search, query):
        """
        Add query part to ``search`` when needed.

        Also:

        * Adds SimpleQueryString instead of default query.
        * Adds HTML encoding of results to avoid XSS issues.
        """
        search = search.highlight_options(encoder='html', number_of_fragments=3)
        search = search.source(exclude=['content', 'headers'])

        all_queries = []

        # need to search for both 'and' and 'or' operations
        # the score of and should be higher as it satisfies both or and and

        for operator in self.operators:
            query_string = SimpleQueryString(
                query=query, fields=self.fields, default_operator=operator
            )
            all_queries.append(query_string)

        # run bool query with should, so it returns result where either of the query matches
        bool_query = Bool(should=all_queries)

        search = search.query(bool_query)
        return search


class ProjectSearchBase(RTDFacetedSearch):
    facets = {'language': TermsFacet(field='language')}
    doc_types = [ProjectDocument]
    index = ProjectDocument._doc_type.index
    fields = ('name^10', 'slug^5', 'description')
    operators = ['and', 'or']


class PageSearchBase(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version'),
        'role_name': NestedFacet(
            'domains',
            TermsFacet(field='domains.role_name')
        ),
    }
    doc_types = [PageDocument]
    index = PageDocument._doc_type.index

    _outer_fields = ['title^4']
    _section_fields = ['sections.title^3', 'sections.content']
    _domain_fields = [
        'domains.type_display',
        'domains.name^2',
        'domains.display_name',
    ]
    fields = _outer_fields

    # need to search for both 'and' and 'or' operations
    # the score of and should be higher as it satisfies both or and and
    operators = ['and', 'or']

    def count(self):
        """Overriding ``count`` method to return the count of the results after post_filter."""
        s = self.build_search()

        # setting size=0 so that no results are returned,
        # we are only interested in the total count
        s = s.extra(size=0)
        s = s.execute()
        return s.hits.total

    def query(self, search, query):
        """Manipulates query to support nested query."""
        search = search.highlight_options(encoder='html', number_of_fragments=1)

        # match query for the title (of the page) field.
        match_title_query = Match(title=query)

        # nested query for search in sections
        sections_nested_query = self.generate_nested_query(
            query=query,
            path='sections',
            fields=self._section_fields,
            inner_hits={
                'highlight': {
                    'encoder': 'html',
                    'number_of_fragments': 1,
                    'fields': {
                        'sections.title': {},
                        'sections.content': {},
                    }
                }
            }
        )

        # nested query for search in domains
        domains_nested_query = self.generate_nested_query(
            query=query,
            path='domains',
            fields=self._domain_fields,
            inner_hits={
                'highlight': {
                    'encoder': 'html',
                    'number_of_fragments': 1,
                    'fields': {
                        'domains.type_display': {},
                        'domains.name': {},
                        'domains.display_name': {},
                    }
                }
            }
        )

        final_query = Bool(should=[
            match_title_query,
            sections_nested_query,
            domains_nested_query,
        ])

        search = search.query(final_query)
        return search

    def generate_nested_query(self, query, path, fields, inner_hits):
        """Generate a nested query with passed parameters."""
        queries = []

        for operator in self.operators:
            query_string = SimpleQueryString(
                query=query,
                fields=fields,
                default_operator=operator
            )
            queries.append(query_string)

        bool_query = Bool(should=queries)

        nested_query = Nested(
            path=path,
            inner_hits=inner_hits,
            query=bool_query
        )
        return nested_query


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
