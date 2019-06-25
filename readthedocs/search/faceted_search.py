import logging

from elasticsearch import Elasticsearch
from elasticsearch_dsl import FacetedSearch, TermsFacet
from elasticsearch_dsl.query import Bool, SimpleQueryString

from django.conf import settings

from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.search.documents import (
    PageDocument,
    ProjectDocument,
    SphinxDomainDocument,
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
        'version': TermsFacet(field='version')
    }
    doc_types = [PageDocument]
    index = PageDocument._doc_type.index
    outer_fields = ['title^10']
    nested_fields = ['sections.title^5', 'sections.content']
    fields = outer_fields
    operators = ['and', 'or']

    def query(self, search, query):
        """Manipulates query to support nested query."""
        search = search.highlight_options(encoder='html', number_of_fragments=3)

        all_queries = []

        # need to search for both 'and' and 'or' operations
        # the score of and should be higher as it satisfies both or and and

        for operator in self.operators:
            query_string = SimpleQueryString(
                query=query,
                fields=self.outer_fields + self.nested_fields,
                default_operator=operator
            )
            all_queries.append(query_string)

        # run bool query with should, so it returns result where either of the query matches
        bool_query = Bool(should=all_queries)

        search = search.query(
            'nested',
            path='sections',
            inner_hits={
                'highlight': {
                    'fields': {
                        'sections.title': {},
                        'sections.content': {},
                    }
                }
            },
            query=bool_query
        )
        return search


class DomainSearchBase(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version'),
        'role_name': TermsFacet(field='role_name'),
    }
    doc_types = [SphinxDomainDocument]
    index = SphinxDomainDocument._doc_type.index
    fields = ('display_name^5', 'name^3', 'project^3', 'type_display')
    operators = ['and']


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


class DomainSearch(SettingsOverrideObject):

    """
    Allow this class to be overridden based on CLASS_OVERRIDES setting.

    This is primary used on the .com to adjust how we filter our search queries
    """

    _default_class = DomainSearchBase


class AllSearch(RTDFacetedSearch):

    """
    Simplfy for testing.

    It has some UI/UX problems that need to be addressed.
    """

    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version'),
        'language': TermsFacet(field='language'),
        'role_name': TermsFacet(field='role_name'),
        # Need to improve UX here for exposing to users
        # 'index': TermsFacet(field='_index'),
    }
    doc_types = [SphinxDomainDocument, PageDocument, ProjectDocument]
    index = [SphinxDomainDocument._doc_type.index,
             PageDocument._doc_type.index,
             ProjectDocument._doc_type.index]
    fields = ('title^10', 'headers^5', 'content', 'name^20',
              'slug^5', 'description', 'display_name^5')
    operators = ['and']
