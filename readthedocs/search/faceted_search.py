import structlog
import re

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import FacetedSearch, TermsFacet
from elasticsearch_dsl.faceted_search import NestedFacet
from elasticsearch_dsl.query import (
    Bool,
    FunctionScore,
    MultiMatch,
    Nested,
    SimpleQueryString,
    Term,
    Terms,
    Wildcard,
)

from readthedocs.search.documents import PageDocument, ProjectDocument

log = structlog.get_logger(__name__)

ALL_FACETS = ['project', 'version', 'role_name', 'language']


class RTDFacetedSearch(FacetedSearch):

    """Custom wrapper around FacetedSearch."""

    # Search for both 'and' and 'or' operators.
    # The score of and should be higher as it satisfies both or and and.
    operators = ['and', 'or']

    # Sources to be excluded from results.
    excludes = []

    _highlight_options = {
        'encoder': 'html',
        'number_of_fragments': 1,
        'pre_tags': ['<span>'],
        'post_tags': ['</span>'],
    }

    def __init__(
            self,
            query=None,
            filters=None,
            projects=None,
            aggregate_results=True,
            use_advanced_query=True,
            **kwargs,
    ):
        """
        Custom wrapper around FacetedSearch.

        :param string query: Query to search for
        :param dict filters: Filters to be used with the query.
        :param projects: A dictionary of project slugs mapped to a `VersionData` object.
         Or a list of project slugs.
         Results are filter with these values.
        :param use_advanced_query: If `True` forces to always use
         `SimpleQueryString` for the text query object.
        :param bool aggregate_results: If results should be aggregated,
         this is returning the number of results within other facets.
        :param bool use_advanced_query: Always use SimpleQueryString.
         Set this to `False` to use the experimental fuzzy search.
        """
        self.use_advanced_query = use_advanced_query
        self.aggregate_results = aggregate_results
        self.projects = projects or {}

        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.info('Hacking Elastic to fix search connection pooling')
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])

        filters = filters or {}

        # We may receive invalid filters
        valid_filters = {
            k: v
            for k, v in filters.items()
            if k in self.facets
        }
        super().__init__(query=query, filters=valid_filters, **kwargs)

    def _get_queries(self, *, query, fields):
        """
        Get a list of query objects according to the query.

        If the query is a single term we try to match partial words and substrings
        (available only with the DEFAULT_TO_FUZZY_SEARCH feature flag),
        otherwise we use the SimpleQueryString query.
        """
        get_queries_function = (
            self._get_single_term_queries
            if self._is_single_term(query)
            else self._get_text_queries
        )

        return get_queries_function(
            query=query,
            fields=fields,
        )

    def _get_text_queries(self, *, query, fields):
        """
        Returns a list of query objects according to the query.

        SimpleQueryString provides a syntax to let advanced users manipulate
        the results explicitly.

        We need to search for both "and" and "or" operators.
        The score of "and" should be higher as it satisfies both "or" and "and".

        For valid options, see:

        - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html  # noqa
        """
        queries = []
        is_advanced_query = self.use_advanced_query or self._is_advanced_query(query)
        for operator in self.operators:
            if is_advanced_query:
                query_string = SimpleQueryString(
                    query=query,
                    fields=fields,
                    default_operator=operator,
                )
            else:
                query_string = self._get_fuzzy_query(
                    query=query,
                    fields=fields,
                    operator=operator,
                )
            queries.append(query_string)
        return queries

    def _get_single_term_queries(self, query, fields):
        """
        Returns a list of query objects for fuzzy and partial results.

        We need to search for both "and" and "or" operators.
        The score of "and" should be higher as it satisfies both "or" and "and".

        We use the Wildcard query with the query suffixed by ``*`` to match substrings.

        For valid options, see:

        - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-wildcard-query.html  # noqa

        .. note::

           Doing a prefix **and** suffix search is slow on big indexes like ours.
        """
        query_string = self._get_fuzzy_query(
            query=query,
            fields=fields,
        )
        queries = [query_string]
        for field in fields:
            # Remove boosting from the field,
            field = re.sub(r'\^.*$', '', field)
            kwargs = {
                field: {'value': f'{query}*'},
            }
            queries.append(Wildcard(**kwargs))
        return queries

    def _get_fuzzy_query(self, *, query, fields, operator='or'):
        """
        Returns a query object used for fuzzy results.

        For valid options, see:

        - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query.html
        """
        return MultiMatch(
            query=query,
            fields=fields,
            operator=operator,
            fuzziness="AUTO:4,6",
            prefix_length=1,
        )

    def _is_single_term(self, query):
        """
        Check if the query is a single term.

        A query is a single term if it is a single word,
        if it doesn't contain the syntax from a simple query string,
        and if `self.use_advanced_query` is False.
        """
        is_single_term = (
            not self.use_advanced_query and
            query and len(query.split()) <= 1 and
            not self._is_advanced_query(query)
        )
        return is_single_term

    def _is_advanced_query(self, query):
        """
        Check if query looks like to be using the syntax from a simple query string.

        .. note::

           We don't check if the syntax is valid.
           The tokens used aren't very common in a normal query, so checking if
           the query contains any of them should be enough to determinate if
           it's an advanced query.

        Simple query syntax:

        https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-simple-query-string-query.html#simple-query-string-syntax
        """
        tokens = {'+', '|', '-', '"', '*', '(', ')', '~'}
        query_tokens = set(query)
        return not tokens.isdisjoint(query_tokens)

    def aggregate(self, search):
        """Overridden to decide if we should aggregate or not."""
        if self.aggregate_results:
            super().aggregate(search)


class ProjectSearch(RTDFacetedSearch):
    facets = {'language': TermsFacet(field='language')}
    doc_types = [ProjectDocument]
    index = ProjectDocument._index._name
    fields = ('name^10', 'slug^5', 'description')
    excludes = ['users', 'language']

    def query(self, search, query):
        """
        Customize search results to support extra functionality.

        If `self.projects` was given, we use it to filter the documents.
        Only filtering by a list of slugs is supported.

        Also:

        * Adds SimpleQueryString with `self.operators` instead of default query.
        * Adds HTML encoding of results to avoid XSS issues.
        """
        search = search.highlight_options(**self._highlight_options)
        search = search.source(excludes=self.excludes)

        queries = self._get_queries(
            query=query,
            fields=self.fields,
        )

        # Run bool query with should, so it returns result where either of the query matches.
        bool_query = Bool(should=queries)

        # Filter by project slugs.
        if self.projects:
            if isinstance(self.projects, list):
                projects_query = Bool(filter=Terms(slug=self.projects))
                bool_query = Bool(must=[bool_query, projects_query])
            else:
                raise ValueError('projects must be a list!')

        search = search.query(bool_query)
        return search


class PageSearch(RTDFacetedSearch):
    facets = {
        'project': TermsFacet(field='project'),
        'version': TermsFacet(field='version'),
        'role_name': NestedFacet(
            'domains',
            TermsFacet(field='domains.role_name')
        ),
    }
    doc_types = [PageDocument]
    index = PageDocument._index._name

    # boosting for these fields need to be close enough
    # to be re-boosted by the page rank.
    _outer_fields = ['title^1.5']
    _section_fields = ['sections.title^2', 'sections.content']
    _domain_fields = [
        'domains.name^1.5',
        'domains.docstrings',
    ]
    fields = _outer_fields
    excludes = ['rank', 'sections', 'domains', 'commit', 'build']

    def _get_projects_query(self):
        """
        Get filter by projects query.

        If it's a dict, filter by project and version,
        if it's a list filter by project.
        """
        if not self.projects:
            return None

        if isinstance(self.projects, dict):
            versions_query = [
                Bool(filter=[Term(project=project), Term(version=version)])
                for project, version in self.projects.items()
            ]
            return Bool(should=versions_query)

        if isinstance(self.projects, list):
            return Bool(filter=Terms(project=self.projects))

        raise ValueError('projects must be a list or a dict!')

    def query(self, search, query):
        """
        Manipulates the query to support nested queries and a custom rank for pages.

        If `self.projects` was given, we use it to filter the documents that
        match the same project and version.
        """
        search = search.highlight_options(**self._highlight_options)
        search = search.source(excludes=self.excludes)

        queries = self._get_queries(
            query=query,
            fields=self.fields,
        )

        sections_nested_query = self._get_nested_query(
            query=query,
            path='sections',
            fields=self._section_fields,
        )

        domains_nested_query = self._get_nested_query(
            query=query,
            path='domains',
            fields=self._domain_fields,
        )

        queries.extend([sections_nested_query, domains_nested_query])
        bool_query = Bool(should=queries)

        projects_query = self._get_projects_query()
        if projects_query:
            bool_query = Bool(must=[bool_query, projects_query])

        final_query = FunctionScore(
            query=bool_query,
            script_score=self._get_script_score(),
        )
        search = search.query(final_query)
        return search

    def _get_nested_query(self, *, query, path, fields):
        """Generate a nested query with passed parameters."""
        queries = self._get_queries(
            query=query,
            fields=fields,
        )
        bool_query = Bool(should=queries)

        raw_fields = [
            # Remove boosting from the field
            re.sub(r'\^.*$', '', field)
            for field in fields
        ]

        # The ``post_filter`` filter will only filter documents
        # at the parent level (domains is a nested document),
        # resulting in results with domains that don't match the current
        # role_name being filtered, so we need to force filtering by role_name
        # on the ``domains`` document here. See #8268.
        # TODO: We should use a flattened document instead
        # to avoid this kind of problems and have faster queries.
        role_name = self.filter_values.get('role_name')
        if path == 'domains' and role_name:
            role_name_query = Bool(must=Terms(**{'domains.role_name': role_name}))
            bool_query = Bool(must=[role_name_query, bool_query])

        highlight = dict(
            self._highlight_options,
            fields={
                field: {}
                for field in raw_fields
            },
        )

        return Nested(
            path=path,
            inner_hits={'highlight': highlight},
            query=bool_query,
        )

    def _get_script_score(self):
        """
        Gets an ES script to map the page rank to a valid score weight.

        ES expects the rank to be a number greater than 0,
        but users can set this between [-10, +10].
        We map that range to [0.01, 2] (21 possible values).

        The first lower rank (0.8) needs to bring the score from the highest boost (sections.title^2)
        close to the lowest boost (title^1.5), that way exact results take priority:

        - 2.0 * 0.8 = 1.6 (score close to 1.5, but not lower than it)
        - 1.5 * 0.8 = 1.2 (score lower than 1.5)

        The first higher rank (1.2) needs to bring the score from the lowest boost (title^1.5)
        close to the highest boost (sections.title^2), that way exact results take priority:

        - 2.0 * 1.3 = 2.6 (score higher thank 2.0)
        - 1.5 * 1.3 = 1.95 (score close to 2.0, but not higher than it)

        The next lower and higher ranks need to decrease/increase both scores.

        See https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-script-score-query.html#field-value-factor  # noqa
        """
        ranking = [
            0.01,
            0.05,
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            1,
            1.3,
            1.4,
            1.5,
            1.6,
            1.7,
            1.8,
            1.9,
            1.93,
            1.96,
            2,
        ]
        # Each rank maps to a element in the ranking list.
        # -10 will map to the first element (-10 + 10 = 0) and so on.
        source = """
            int rank = doc['rank'].size() == 0 ? 0 : (int) doc['rank'].value;
            return params.ranking[rank + 10] * _score;
        """
        return {
            "script": {
                "source": source,
                "params": {"ranking": ranking},
            },
        }
