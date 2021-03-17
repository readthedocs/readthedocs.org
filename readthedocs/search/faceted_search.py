import logging
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
    Wildcard,
)

from readthedocs.analytics.models import PageView
from readthedocs.core.utils.extend import SettingsOverrideObject
from readthedocs.search.documents import PageDocument, ProjectDocument

log = logging.getLogger(__name__)

ALL_FACETS = ['project', 'version', 'role_name', 'language', 'index']


class RTDFacetedSearch(FacetedSearch):

    """Custom wrapper around FacetedSearch."""

    operators = []

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
            user=None,
            use_advanced_query=True,
            use_page_views=False,
            **kwargs,
    ):
        """
        Pass in a user in order to filter search results by privacy.

        :param projects: A dictionary of project slugs mapped to a `VersionData` object.
        Results are filter with these values.

        :param use_advanced_query: If `True` forces to always use
        `SimpleQueryString` for the text query object.

        If `use_page_views` is `True`,
        weight page views into the search results.

        .. warning::

            The `self.user` and `self.filter_by_user` attributes
            aren't currently used on the .org, but are used on the .com.
        """
        self.user = user
        self.filter_by_user = kwargs.pop('filter_by_user', True)
        self.use_advanced_query = use_advanced_query
        self.projects = projects or {}
        self.use_page_views = use_page_views

        # Hack a fix to our broken connection pooling
        # This creates a new connection on every request,
        # but actually works :)
        log.info('Hacking Elastic to fix search connection pooling')
        self.using = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])

        filters = filters or {}

        # We may recieve invalid filters
        valid_filters = {
            k: v
            for k, v in filters.items()
            if k in self.facets
        }
        super().__init__(query=query, filters=valid_filters, **kwargs)

    def _get_queries(self, *, query, fields):
        """
        Get a list of query objects according to the query.

        If the query is a *single term* (a single word)
        we try to match partial words and substrings
        (available only with the DEFAULT_TO_FUZZY_SEARCH feature flag).

        If the query is a phrase or contains the syntax from a simple query string,
        we use the SimpleQueryString query.
        """
        is_single_term = (
            not self.use_advanced_query and
            query and len(query.split()) <= 1 and
            not self._is_advanced_query(query)
        )
        get_queries_function = (
            self._get_single_term_queries
            if is_single_term
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

        We use the Wildcard query with the query surrounded by ``*`` to match substrings.

        For valid options, see:

        - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-wildcard-query.html  # noqa
        """
        queries = []
        for operator in self.operators:
            query_string = self._get_fuzzy_query(
                query=query,
                fields=fields,
                operator=operator,
            )
            queries.append(query_string)
        for field in fields:
            # Remove boosting from the field
            field = re.sub(r'\^.*$', '', field)
            kwargs = {
                field: {'value': f'*{query}*'},
            }
            queries.append(Wildcard(**kwargs))
        return queries

    def _get_fuzzy_query(self, *, query, fields, operator):
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

    def query(self, search, query):
        """
        Add query part to ``search`` when needed.

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

        # run bool query with should, so it returns result where either of the query matches
        bool_query = Bool(should=queries)
        search = search.query(bool_query)
        return search


class ProjectSearchBase(RTDFacetedSearch):
    facets = {'language': TermsFacet(field='language')}
    doc_types = [ProjectDocument]
    index = ProjectDocument._index._name
    fields = ('name^10', 'slug^5', 'description')
    operators = ['and', 'or']
    excludes = ['users', 'language']


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

    # need to search for both 'and' and 'or' operations
    # the score of and should be higher as it satisfies both or and and
    operators = ['and', 'or']

    excludes = ['rank', 'sections', 'domains', 'commit', 'build']

    def total_count(self):
        """Returns the total count of results of the current query."""
        s = self.build_search()

        # setting size=0 so that no results are returned,
        # we are only interested in the total count
        s = s.extra(size=0)
        s = s.execute()
        return s.hits.total['value']

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

        if self.projects:
            versions_query = [
                Bool(
                    must=[
                        Term(project={'value': project}),
                        Term(version={'value': version}),
                    ]
                )
                for project, version in self.projects.items()
            ]
            bool_query = Bool(must=[bool_query, Bool(should=versions_query)])

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

        raw_fields = (
            # Remove boosting from the field
            re.sub(r'\^.*$', '', field)
            for field in fields
        )

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
            query=Bool(should=queries),
        )

    def _get_script_score(self):
        """
        Gets an ES script that combines the page rank and views into the final score.

        **Page ranking weight calculation**

        Each rank maps to an element in the ranking list.
        -10 will map to the first element (-10 + 10 = 0) and so on.

        **Page views weight calculation**

        We calculate two values:

        - absolute: this is equal to ``log10(views + 1)``
          (we add one since logarithms start at 1).
          A logarithmic function is a good fit due to its growth rate.
        - relative: this is equal to the ratio between the number of views of the current page
          and the max number of views of the current version.

        Those two values are added and multiplied by a weight (``views_factor``).

        .. note::

           We can also make use of the ratio between the number of views
           and the average of views of the current version.

        **Final score**

        To generate the final score,
        all weights are added and multiplied by the original score.

        Docs about the script score query and the painless language at:

        - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-script-score-query.html#field-value-factor  # noqa
        - https://www.elastic.co/guide/en/elasticsearch/painless/6.8/painless-api-reference.html
        """
        source = """
            // Page ranking weight.
            int rank = doc['rank'].size() == 0 ? 0 : (int) doc['rank'].value;
            double ranking = params.ranking[rank + 10];

            // Page views weight.
            int views = 0;
            int max_views = 0;
            String project = doc['project'].value;
            String version = doc['version'].value;
            String path = doc['full_path'].value;

            Map pages = params.top_pages.get(project);
            if (pages != null) {
                pages = pages.get(version);
                if (pages != null) {
                    views = (int) pages.get("pages").getOrDefault(path, 0);
                    max_views = (int) pages.get("max");
                }
            }
            double absolute_views = Math.log10(views + 1);
            double relative_views = 0;
            if (max_views > 0) {
                relative_views = views/max_views;
            }
            double views_weight = (absolute_views + relative_views) * params.views_factor;

            // Combine all weights into a final score.
            return (ranking + views_weight) * _score;
        """
        return {
            "script": {
                "source": source,
                "params": {
                    "ranking": self._get_ranking(),
                    "top_pages": self._get_top_pages(),
                    "views_factor": 1/10,
                },
            },
        }

    def _get_ranking(self):
        """
        Get ranking for pages.

        ES expects the rank to be a number greater than 0,
        but users can set this between [-10, +10].
        We map that range to [0.01, 2] (21 possible values).

        The first lower rank (0.8) needs to bring the score from the highest boost
        (sections.title^2) close to the lowest boost (title^1.5), that way exact
        results can still take priority:

        - 2.0 * 0.8 = 1.6 (score close to 1.5, but not lower than it)
        - 1.5 * 0.8 = 1.2 (score lower than 1.5)

        The first higher rank (1.2) needs to bring the score from the lowest boost (title^1.5)
        close to the highest boost (sections.title^2), that way exact results take priority:

        - 2.0 * 1.3 = 2.6 (score higher thank 2.0)
        - 1.5 * 1.3 = 1.95 (score close to 2.0, but not higher than it)

        The next lower and higher ranks need to decrease/increase both scores.
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
        return ranking

    def _get_top_pages(self):
        """
        Get the top 100 pages for the versions of the current projects.

        Returns a dictionary with the following structure:

            {
                'project': {
                    'version': {
                        'max': max_views,
                        'pages': {
                            'page': views,
                        },
                    },
                },
            }

        The number of views can be between 0 and 2**31 - 9,
        this is so we don't overflow when casting the value to an integer
        inside ES, this also gives us a max value to work on and some space for
        additional operations.
        """
        try:
            if not self.use_page_views:
                return {}

            project = self.filter_values['project'][0]
            version = self.filter_values['version'][0]
            top_pages_data = PageView.top_viewed_pages(
                project_slug=project,
                version_slug=version,
                top=100,
            )
            if not top_pages_data['pages'] or not top_pages_data['view_counts']:
                return {}

            max_int = 2**31 - 9
            top_pages_for_version = {
                page: min(views, max_int)
                for page, views in zip(top_pages_data['pages'], top_pages_data['view_counts'])
            }
            top_pages = {
                project: {version: {'pages': top_pages_for_version}}
            }

            # Calculate the max views from each version.
            for project_data in top_pages.values():
                for version_data in project_data.values():
                    pages = version_data['pages']
                    max_ = max(pages.values())
                    version_data['max'] = max_
            return top_pages
        except (KeyError, IndexError):
            return {}


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
