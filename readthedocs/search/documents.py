from django.conf import settings
from django_elasticsearch_dsl import DocType, Index, fields
from elasticsearch_dsl.query import SimpleQueryString, Bool

from readthedocs.projects.models import Project, HTMLFile
from readthedocs.search.faceted_search import ProjectSearch, FileSearch
from .mixins import RTDDocTypeMixin

project_conf = settings.ES_INDEXES['project']
project_index = Index(project_conf['name'])
project_index.settings(**project_conf['settings'])

page_conf = settings.ES_INDEXES['page']
page_index = Index(page_conf['name'])
page_index.settings(**page_conf['settings'])


@project_index.doc_type
class ProjectDocument(RTDDocTypeMixin, DocType):

    class Meta(object):
        model = Project
        fields = ('name', 'slug', 'description')
        ignore_signals = settings.ES_PROJECT_IGNORE_SIGNALS

    url = fields.TextField(attr='get_absolute_url')
    users = fields.NestedField(properties={
        'username': fields.TextField(),
        'id': fields.IntegerField(),
    })
    language = fields.KeywordField()

    @classmethod
    def faceted_search(cls, query, language=None, using=None, index=None):
        kwargs = {
            'using': using or cls._doc_type.using,
            'index': index or cls._doc_type.index,
            'doc_types': [cls],
            'model': cls._doc_type.model,
            'query': query
        }

        if language:
            kwargs['filters'] = {'language': language}

        return ProjectSearch(**kwargs)


@page_index.doc_type
class PageDocument(RTDDocTypeMixin, DocType):

    class Meta(object):
        model = HTMLFile
        fields = ('commit',)
        ignore_signals = settings.ES_PAGE_IGNORE_SIGNALS

    project = fields.KeywordField(attr='project.slug')
    version = fields.KeywordField(attr='version.slug')

    title = fields.TextField(attr='processed_json.title')
    headers = fields.TextField(attr='processed_json.headers')
    content = fields.TextField(attr='processed_json.content')
    path = fields.KeywordField(attr='processed_json.path')

    # Fields to perform search with weight
    search_fields = ['title^10', 'headers^5', 'content']
    # Exclude some files to not index
    excluded_files = ['search.html', 'genindex.html', 'py-modindex.html',
                      'search/index.html', 'genindex/index.html', 'py-modindex/index.html']

    @classmethod
    def faceted_search(cls, query, projects_list=None, versions_list=None, using=None, index=None):
        es_query = cls.get_es_query(query=query)
        kwargs = {
            'using': using or cls._doc_type.using,
            'index': index or cls._doc_type.index,
            'doc_types': [cls],
            'model': cls._doc_type.model,
            'query': es_query,
            'fields': cls.search_fields
        }
        filters = {}

        if projects_list:
            filters['project'] = projects_list
        if versions_list:
            filters['version'] = versions_list

        kwargs['filters'] = filters

        return FileSearch(**kwargs)

    @classmethod
    def simple_search(cls, query, using=None, index=None):
        """
        Do a search without facets.

        This is used in:

        * The Docsearch API
        * The Project Admin Search page
        """

        es_search = cls.search(using=using, index=index)
        es_search = es_search.highlight_options(encoder='html')

        es_query = cls.get_es_query(query=query)
        highlighted_fields = [f.split('^', 1)[0] for f in cls.search_fields]
        es_search = es_search.query(es_query).highlight(*highlighted_fields)

        return es_search

    @classmethod
    def get_es_query(cls, query):
        """Return the Elasticsearch query generated from the query string"""
        all_queries = []

        # Need to search for both 'AND' and 'OR' operations
        # The score of AND should be higher as it satisfies both OR and AND
        for operator in ['AND', 'OR']:
            query_string = SimpleQueryString(query=query, fields=cls.search_fields,
                                             default_operator=operator)
            all_queries.append(query_string)

        # Run bool query with should, so it returns result where either of the query matches
        bool_query = Bool(should=all_queries)

        return bool_query

    def get_queryset(self):
        """Overwrite default queryset to filter certain files to index"""
        queryset = super(PageDocument, self).get_queryset()

        # Do not index files that belong to non sphinx project
        # Also do not index certain files
        queryset = queryset.filter(project__documentation_type__contains='sphinx')
        for ending in self.excluded_files:
            queryset = queryset.exclude(path__endswith=ending)
        return queryset
